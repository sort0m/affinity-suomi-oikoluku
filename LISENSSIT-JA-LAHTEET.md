# Lisenssit ja lähdekoodi

Affinity-oikoluku 1.7 on tämän projektin sovellus. Voikko on sen käyttämä
erillinen oikolukukirjasto ja sanasto. Tavutustiedosto perustuu Mika Vainion
AffinityPublisherFISpelling-projektin tiedostoon, ja siihen on tehty muutoksia.

| Osa | Lisenssi ja alkuperä | Tässä jakelussa |
| --- | --- | --- |
| Sovelluksen Python- ja JavaScript-koodi sekä muokattu tavutustiedosto | GNU GPL 3; tavutustiedoston pohja: [Mika Vainion projekti](https://github.com/MikaVainio/AffinityPublisherFISpelling) | Repositorion `LICENSE`, lähdekoodi sekä ZIPin `Lisenssit/Projekti-GPL3.txt` ja `Lisenssit/Sovelluksen-lahdekoodi.zip` |
| libvoikko 4.3+win1 ja `libvoikko.py` | MPL 1.1 / GPL 2 tai uudempi / LGPL 2.1 tai uudempi. Tässä jakelussa käytetään GPL 3 -vaihtoehtoa. [Virallinen Windows-jakelu](https://www.puimula.org/htp/testing/voikko-sdk/win-crossbuild/libvoikko-4.3%2Bwin1/) | ZIPin `Lisenssit/libvoikko-4.3+win1.tar.gz` sisältää lähdekoodin sekä `COPYING`- ja `LICENSE.CORE`-tiedostot. `Lisenssit/libvoikko-rajapinta.py` on käytetty Python-sidos. |
| Voikon suomen perussanasto, tilanne 18.6.2024 | GPL 2 tai uudempi; tekijätiedot ovat sanaston `index.txt`-tiedostossa. Tässä jakelussa käytetään GPL 3 -vaihtoehtoa. [Virallinen sanastosivu](https://www.puimula.org/htp/testing/voikko-snapshot-v5/) | ZIPin `Lisenssit/voikko-fi-snapshot.tar.gz` sisältää lähdekoodin, `COPYING`- ja `CONTRIBUTORS`-tiedostot. Käytetyn binäärisanaston `index.txt` on `_internal/assets/5/mor-standard/`-kansiossa. |
| Python 3.14.3 ja sen mukana toimitetut osat, esimerkiksi OpenSSL 3.0.18 | Python Software Foundation License 2; mukana olevien osien ehdot on koottu Pythonin lisenssitiedostoon. OpenSSL 3 kuuluu Apache 2.0 -lisenssiin. [Pythonin lisenssitiedot](https://docs.python.org/3.14/license.html) | ZIPin `Lisenssit/Python.txt` |
| PyInstaller 6.19.0 -käynnistin | GPL 2 tai uudempi, käynnistimen poikkeus. [PyInstallerin lisenssi](https://pyinstaller.org/en/stable/license.html) | ZIPin `Lisenssit/PyInstaller.txt` |

ZIPissä olevien Voikko-osien vastaavat lähdekoodipaketit ovat myös repositorion
`kolmannen_osapuolen_lahdekoodi/`-kansiossa. Ne ladattiin yllä linkitetyiltä
Voikko-projektin sivuilta. Lähdekoodipakettien SHA-256-tiivisteet:

```text
libvoikko-4.3+win1.tar.gz  594480de1e3611c63d20c2e1d159041aed18ca458dd272e9d7daa783362f4f89
voikko-fi-snapshot.tar.gz  a22dc3f9d506e7d7d2022d7854abcae459818df0bd7a9de016e78992f4f535c1
```

Sovelluksen oma lähdekoodi, tavutussääntöjen muokattava
`hyphenation_patterns.txt` sekä rakentamisohje ovat repositoriossa ja ZIPin
`Lisenssit/Sovelluksen-lahdekoodi.zip`-tiedostossa. Käytetyn valmiin
Voikko-kirjaston ja sanaston lähdekoodit ovat yllä mainituissa tar.gz-paketeissa.
