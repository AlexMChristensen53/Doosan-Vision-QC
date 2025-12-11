1. Sådan starter du Vision QC Systemet

Naviger først til projektmappen:
cd E_tests/JacobV_test


Start programmet:
python qc_main.py


Du vil se følgende menu:
1. Commands info
2. Start QC pipeline
3. Quit


Vælg:
2


Programmet vil nu:
Starte OAK-D kameraet
Læse QC-indstillinger
Detektere objekter
Køre QC-moduler
Beregne orientering og robotpositioner
Vise grafiske debug-vinduer

2. Tastaturkontrol (QC-loop) (Kamera vindue skal være aktivt for at bruge disse kommandoer)
Tast	Funktion
u	Print FORM debug
i	Print SIZE debug
o	Print COLOR debug
p	Print SPECIAL debug
r	Print robot-payload
s	Print beregnede positioner og vinkler
g	Print frame-shapes
e	Eksporter robot_commands.json
m	Tilbage til main menu
q	Afslut program

3. Sortering af emner
Når vores QC Pipeline er startet, vil robotten hele tiden stå og læse ind i robot_commands.json
hvis den detekterer ændringer heri altså ved (e) ny export begynder robotten at indlæse commandoerne linje for linje og ligge dem i en kø.

