const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const core = require('../voikko/affinity-voikko.js');

function story(text) {
    const glyphs = Array.from(text).map(string => ({isCharGlyph: true, string}));
    return {length: glyphs.length, glyphs, getGlyph: i => glyphs[i]};
}

test('glyph positions survive emoji, fields, paragraphs and repeated words', () => {
    const s = story('😀 kissa kissa\näiti');
    s.glyphs[7] = {isCharGlyph: false};
    const snap = core.snapshot(s, 0, s.length);
    const words = core.words(snap);
    assert.deepEqual(words.map(w => [w.word,w.begin,w.end]),
        [['kissa',2,7],['kissa',8,13],['äiti',14,18]]);
});

test('Finnish compounds and combining marks are kept together', () => {
    const s = story('EU-maissa vaa’an a\u0308iti');
    assert.deepEqual(core.words(core.snapshot(s,0,s.length)).map(w=>w.word),
        ['EU-maissa','vaa’an','a\u0308iti']);
    assert.equal(core.replacementAllowed('kaksi sanaa'), false);
    assert.equal(core.replacementAllowed('sana\nuusi'), false);
});

test('batches deduplicate and bound encoded request sizes', () => {
    const input = Array.from({length:140}, (_,i) => 'ää'.repeat(40) + String.fromCharCode(0x400+i));
    const batches = core.batches(input.concat(input));
    assert.equal(batches.flat().length,140);
    for (const batch of batches) {
        assert.ok(batch.length<=40);
        assert.ok(encodeURIComponent(JSON.stringify(batch)).length<12000);
    }
});

// Full orchestration tests use strict SDK-like controls: unknown properties fail
// rather than silently accepting non-existent APIs.
function runScript({cancel=false, changeText=false, mixed=false, failRequest=false,
    wrapped=false, emptySelection=false, locked=false, linked=false, acrossPages=false,
    chooseSuggestion=false, addWord=false}={}) {
    const s = story('kissa kisssa ja kisssa');
    s.isTable = false;
    s.getGlyphAttsRunEnd = (b,e) => mixed ? b+1 : e;
    s.getGlyphAtts = () => ({font:'OriginalFont',size:12});
    const node = {isTextNode:true,isEditable:!locked,isFrameTextNode:linked,
        isSameNode(other) {return this===other;},storyInterface:{story:s}};
    const second={...node,storyInterface:{story:s,storyRange:{begin:16,end:s.length}}};
    if(linked){
        node.storyInterface.storyRange={begin:0,end:16};
        node.textFrameInterface=second.textFrameInterface={textFlowNodes:[node,second]};
    }
    const root=wrapped?{children:[node,...(linked?[second]:[])],isLocalEditable:true}:node;
    const spread={children:[root],isSameNode(other){return this===other;}};
    const otherSpread={isSameNode(other){return this===other;}};
    if(acrossPages){node.spread=spread;second.spread=otherSpread;}
    const alerts=[], edits=[], previews=[], navigation=[], learned=[];
    let previewActive = false;
    const doc = {selection:{nodes:emptySelection?[]:[root]},currentSpread:spread,isSameObject:d=>d===doc,
        clearPreviews(){previewActive=false;},
        executeCommand(command,preview){
            if(command.type==='navigate'){
                assert.notEqual(preview,true,'Viewport navigation cannot be a preview');
                assert.equal(previewActive,false);
                navigation.push(command.spread);this.currentSpread=command.spread;
            }
            else if(preview){
                assert.ok(!command.some(c=>c.type==='navigate'));
                previews.push(command);previewActive=true;
            }
            else {assert.equal(previewActive,false);edits.push(command);}
        }};
    const controls = [];
    function control(label, init={}) {
        const obj = {label,isEnabled:true,isVisible:true,isFullWidth:false,text:'',selectedIndex:0,
            alignment:0,textHorizontalAlignment:0,
            onValueChangedHandler:null,onClickHandler:null,...init};
        controls.push(obj); return Object.seal(obj);
    }
    const group={
        addStaticText:(l,t)=>control(l,{text:t}),
        addComboBox:l=>control(l),
        addTextBox:(l,t)=>control(l,{text:t,kind:'textbox'}),
        addButton:l=>control(l),
        addColumnStack:()=>Object.seal({isVisible:true,addColumn:()=>({widthProportion:1,addGroup:()=>group})}),
    };
    const modules={
        '/application.js':{app:{alert:(m)=>alerts.push(m)}},
        '/document.js':{Document:{current:doc}},
        '/selections.js':{Selection:{create:(d,n)=>({nodes:Array.isArray(n)?n:[n],
            addSubSelectionForNode(node,range){this.range=range;}})},
            TextSelection:{create:range=>range}},
        'affinity:story':{StoryRange:class {constructor(begin,end){this.begin=begin;this.end=end;}}},
        '/commands.js':{DocumentCommand:{
            createSetCurrentSpread:spread=>({type:'navigate',spread}),
            createSetSelection:sel=>({type:'selection',sel}),
            createSetText:(sel,text)=>({type:'text',sel,text}),
            createFormatText:(sel,style)=>({type:'format',sel,style})},
            CompoundCommandBuilder:{create:()=>({commands:[],addCommand(c){this.commands.push(c);},
                createCommand(){return this.commands;}})}},
        '/storydelta.js':{StoryDelta:{createFromGlyphAtts:a=>a,createHighlightFill:a=>a}},
        '/fills.js':{FillDescriptor:{createSolid:c=>c}},
        '/colours.js':{SVG11:{yellow:'yellow'}},
        'affinity:common':{BlendMode:{Normal:0}},
        '/dialog.js':{HorizontalAlignment:{Left:0,Right:2},DialogResult:{Ok:1},Dialog:{create:()=>({initialWidth:0,
            addColumn:()=>({addGroup:()=>group}),runModal(){
                const button=controls.find(c=>c.label==='Korvaa ja seuraava');
                if(chooseSuggestion){
                    const choices=controls.filter(c=>c.label==='Valitse');
                    assert.equal(choices.length,8);
                    choices[1].onClickHandler();
                    assert.equal(controls.find(c=>c.kind==='textbox').text,'kissoja');
                    assert.equal(edits.length,0,'Selecting a suggestion must not commit changes');
                }
                if(addWord){
                    controls.find(c=>c.label==='Lisää sanastoon').onClickHandler();
                    assert.equal(controls.find(c=>c.label==='Lisää sanastoon').isEnabled,false);
                    return 1;
                }
                button.onClickHandler(); button.onClickHandler();
                if(changeText) s.glyphs[0].string='X';
                return cancel?0:1;
            }})}},
        '/network.js':{RequestMethod:{Get:0,Post:1},HttpRequest:{create:(url,method)=>({
            setHeaderValue(){},setTimeoutInSec(){},
            do(){
                if(failRequest) throw new Error('connection failed');
                if(new URL(url).pathname==='/add'){
                    assert.equal(method,1);
                    learned.push(new URL(url).searchParams.get('word'));
                    return {response:{isSuccess:true,content:JSON.stringify({added:true})}};
                }
                if(new URL(url).pathname==='/suggest')
                    return {response:{isSuccess:true,content:JSON.stringify({suggestions:['kissa','kissoja']})}};
                const words=JSON.parse(new URL(url).searchParams.get('words'));
                return {response:{isSuccess:true,content:JSON.stringify({results:words.map(word=>
                    ({word,correct:word!=='kisssa'}))})}};
            }
        })}}
    };
    vm.runInNewContext(fs.readFileSync(require.resolve('../voikko/affinity-voikko.js'),'utf8')
        .replace('"__VOIKKO_KEY__"', '"test-key"'),
        {require:name=>{assert.ok(modules[name],name);return modules[name];},TextDecoder,Uint8Array});
    assert.equal(previewActive,false,'Temporary highlight must be removed');
    return {edits,alerts,previews,node,second,controls,navigation,learned};
}

test('add to dictionary learns the word and skips its remaining occurrences',()=>{
    const result=runScript({addWord:true});
    assert.deepEqual(result.learned,['kisssa']);
    assert.equal(result.edits.length,0);
});

test('accepted fixes apply backwards in one undo and preserve glyph style',()=>{
    const {edits}=runScript();
    assert.equal(edits.length,1);
    assert.equal(edits[0].length,5);
    assert.equal(edits[0][4].type,'selection');
    assert.deepEqual(edits[0].filter(e=>e.type==='text').map(e=>e.sel.range.begin),[16,6]);
    assert.equal(edits[0][1].style.font,'OriginalFont');
});
test('cancel leaves the document untouched',()=>assert.equal(runScript({cancel:true}).edits.length,0));
test('suggestion button picks its word and the next occurrence resets the choice',()=>{
    const r=runScript({chooseSuggestion:true});
    assert.deepEqual(r.edits[0].filter(c=>c.type==='text').map(c=>c.text),['kissa','kissoja']);
    assert.ok(!r.controls.some(c=>c.label==='Sijainti'||c.label==='Valitse ehdotus'));
    assert.ok(r.controls.filter(c=>c.label==='Valitse').every(c=>!c.isEnabled));
});
test('stale text aborts every queued correction',()=>{
    const r=runScript({changeText:true}); assert.equal(r.edits.length,0);
    assert.ok(r.alerts.some(s=>s.includes('Teksti muuttui')));
});
test('mixed formatting inside a word is not flattened',()=>{
    const r=runScript({mixed:true}); assert.equal(r.edits.length,0);
    assert.ok(r.alerts.some(s=>s.includes('eri muotoiluja')));
});
test('connection failure makes no document changes',()=>assert.equal(runScript({failRequest:true}).edits.length,0));

test('master wrapper and empty SDK selection both find page-instance text',()=>{
    for(const emptySelection of [false,true]){
        const r=runScript({wrapped:true,emptySelection});
        assert.equal(r.edits.length,1);
        assert.ok(r.edits[0].filter(c=>c.type==='text').every(c=>c.sel.nodes[0]===r.node));
    }
    assert.equal(runScript({wrapped:true,emptySelection:true,locked:true}).edits.length,0);
});
test('linked story is checked once and highlights the frame containing each occurrence',()=>{
    const r=runScript({wrapped:true,linked:true});
    assert.equal(r.previews.length,2);
    assert.equal(r.previews[0].find(c=>c.type==='format').sel.nodes[0],r.node);
    assert.equal(r.previews[1].find(c=>c.type==='format').sel.nodes[0],r.second);
    assert.deepEqual(r.edits[0].filter(c=>c.type==='text').map(c=>c.sel.nodes[0]),[r.second,r.node]);
});
test('multi-page text navigates outside preview, including the initially active page',()=>{
    const r=runScript({linked:true,acrossPages:true,cancel:true});
    assert.deepEqual(r.navigation,[r.node.spread,r.second.spread]);
    assert.equal(r.edits.length,0);
    assert.equal(r.previews.length,2);
});
