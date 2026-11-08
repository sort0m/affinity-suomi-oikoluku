# Suomen tavutus Affinityyn

Tämä paketti sisältää suomen automaattisen tavutuksen sääntötiedoston
Affinityyn. Affinity 3 yhdistää aiempien Publisher-, Photo- ja Designer-sovellusten
työkalut samaan sovellukseen. Käyttöön tarvitaan vain `hyph_fi_FI.dic`.

## Sanastokansion sijainti

Tarkista ensin Affinityn **Settings > Tools** -kohdasta
**Additional dictionary folder**. Jos siihen on valittu oma kansio, käytä sitä.
Windowsissa asetukset löytyvät yleensä **Edit > Settings** -valikosta ja
macOS:ssä sovelluksen nimellä alkavasta valikosta.

Tavallisia sijainteja ovat:

| Järjestelmä ja versio | Suomen tavutuskansio |
| --- | --- |
| Windows, aiempi Affinity 1 | `C:\ProgramData\Affinity\Common\1.0\Dictionaries\fi_FI` |
| Windows, aiempi Affinity 2 | `C:\ProgramData\Affinity\Common\2.0\Dictionaries\fi_FI` |
| Windows, nykyinen Affinity 3 | `C:\ProgramData\Affinity\Common\3.0\Dictionaries\fi_FI` |
| macOS, aiempi Publisher 2 | `~/Library/Spelling/fi-FI` |

`ProgramData` ja käyttäjän `Library` voivat olla piilotettuja. Voit avata
Windows-polun liittämällä sen Resurssienhallinnan osoiteriville ja macOS-polun
Finderin **Go > Go to Folder** -toiminnolla. Luo puuttuva `Dictionaries`- tai
suomen kielikansio tarvittaessa. Asennustapa, sovellusversio tai itse valittu
lisäsanastokansio voi muuttaa sijaintia.

## Asennus

1. Avaa Affinityn asetuksissa valittu sanastokansio tai yllä oleva versiosi
   tavallinen sijainti.
2. Luo sanastokansioon suomen kielikansio, jos sitä ei vielä ole. Windowsissa
   sen nimi on `fi_FI` ja macOS:ssä `fi-FI`.
3. Jos kielikansiossa on jo `hyph_fi_FI.dic`, ota siitä varmuuskopio. Kopioi
   tämän paketin `hyph_fi_FI.dic` kielikansioon.
4. Käynnistä Affinity uudelleen ja ota tavutus käyttöön alla olevan ohjeen mukaan.
5. Tarkista asiakirjan rivijako: uusi tavutus voi muuttaa taittoa.

## Tavutuksen käyttö Affinityssä

1. Valitse tekstikehys. Kehyksen sisältämää tekstiä ei tarvitse valita erikseen.
2. Avaa **Character > Language** ja valitse **Hyphenation**-kohdassa
   **Finnish (Finland)**.
3. Avaa **Paragraph > Hyphenation** ja ota **Use auto-hyphenation** käyttöön.

Tiedosto on UTF-8-koodattu, ja sen ensimmäisen rivin on pysyttävä `UTF-8`.
Affinity voi rajoittaa katkaisukohtia omilla asetuksillaan. Säännöt eivät
tunnista kaikkia yhdyssanoja tai monitulkintaisia sanoja.

## Sisältö ja lähde

- `hyph_fi_FI.dic` on Affinityyn asennettava tavutustiedosto.
- `hyphenation_patterns.txt` on muokattava sääntölähde.
- `tools/build_hyphenation.py` luo tavutustiedoston lähteestä Python 3:lla.
- `tools/build_hyphenation_release.py` luo tämän jakelupaketin.
- `LICENSE` sisältää GNU GPL 3 -lisenssin.

Tavutus pohjautuu [Mika Vainion AffinityPublisherFISpelling-projektiin](https://github.com/MikaVainio/AffinityPublisherFISpelling),
joka on julkaistu GPL-3.0-lisenssillä. Sen tavutuskuvioiden pohjana ovat
Kauko Saarisen suomalaiset TeX-kuviot (`fihyph.tex`); Fred Karlsson lisäsi
niihin vokaaliyhdistelmiä. [CTAN merkitsee alkuperäisen `fihyph`-paketin
public domain -aineistoksi](https://www.ctan.org/tex-archive/language/hyphenation/fihyph).
Vainion README:n Debianin `myspell-fi` 0.7-18 -viittaus koskee sen
oikeinkirjoitussanastoa: viitatussa hakemistossa ei ole tavutustiedostoa.

Tämä on 8.11.2026 koottu muokattu versio: tavutussääntöjä on
korjattu ja lisätty, tiedoston merkistömäärittely on vaihdettu UTF-8:aan sekä
muokattava sääntölähde ja rakennustyökalut on lisätty pakettiin. Korjattuja
esimerkkejä ovat `vuok-ra`, `kan-san-elä-ke`, `ih-mis-oi-keus` ja `osa-puo-li`.
Tämä muokattu paketti julkaistaan GNU GPL 3 -lisenssillä.
Projektin 265 esimerkkisanaa ja sääntöjen tekninen vertailu 87 643 hakusanalla
menivät läpi. Koko aineiston kielellistä oikeellisuutta tai Affinityn
todellista rivijakoa ei ole todennettu.

Säännöt voi rakentaa uudelleen paketin juuressa komennolla
`python tools/build_hyphenation.py`. Tämä korvaa samassa kansiossa olevan
`hyph_fi_FI.dic`-tiedoston.
