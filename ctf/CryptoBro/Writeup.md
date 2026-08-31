# CryptoBro en détresse — Write-up

**FCSC 2025 — hardware / side channel — flag : `FCSC{9466}`**

---

Avant de commencer j'ai regardé quelques vidéos sur les attaques par analyse de consommation pour mieux comprendre le sujet, notamment celle-ci : https://www.youtube.com/watch?v=8VO21xecC8Q. En gros l'idée c'est qu'un circuit ne consomme pas la même quantité de courant selon les instructions qu'il exécute, du coup si on regarde la consommation on peut deviner ce que le programme est en train de faire. C'est ça qu'on va exploiter ici : on a 10 000 traces d'oscilloscope, une par PIN testé, et il faut retrouver le bon.

## Premier coup d'œil

Je décompresse et je compte les fichiers :

```bash
tar -xJf cryptobro.tar.xz
cd traces
ls | wc -l
```

```
9999
```

Bizarre, je m'attendais à 10 000 (de 0000 à 9999). Il en manque un, je regarde lequel :

```python
import glob, os
pins = {os.path.basename(f)[6:10] for f in glob.glob('trace_*.npy')}
print({'%04d' % i for i in range(10000)} - pins)
```

```
{'0000'}
```

C'est `trace_0000.npy` qui n'est pas là. Je note dans un coin, ça élimine déjà une possibilité.

Ensuite je regarde à quoi ressemble une trace :

```python
import numpy as np
t = np.load('trace_0001.npy')
print(t.dtype, t.shape)
print(t[:10])
```

```
float64 (100,)
[ 0.21484375  0.06640625  0.29296875 -0.1171875   0.03515625
  0.19921875  0.1640625  -0.140625   -0.078125   -0.10546875]
```

100 valeurs en float64. À l'œil nu ça ne veut rien dire, c'est juste du signal.

## Ma première idée, qui tombe à l'eau

L'attaque classique dans ce genre de cas, c'est de jouer sur le **temps**. Le code qui vérifie le PIN ressemble sûrement à ça :

```c
for (int i = 0; i < 4; i++) {
    if (saisie[i] != pin[i]) return FAUX;   // il s'arrête au premier chiffre faux
}
return VRAI;
```

Donc plus on a de chiffres corrects, plus le programme tourne longtemps. Il suffirait de chercher la trace la plus longue.

Je vérifie :

```python
shapes = {np.load(f, mmap_mode='r').shape for f in glob.glob('trace_*.npy')}
print(shapes)
```

```
{(100,)}
```

Bon, ça ne marche pas. Toutes les traces font pile 100 points.

En relisant l'énoncé je comprends pourquoi : l'alimentation est coupée après un délai fixe. Donc peu importe combien de temps le programme met vraiment, l'oscilloscope enregistre toujours la même durée. Ça veut dire que si l'info est quelque part, elle est dans la **forme** du signal et pas dans sa longueur.

## Chercher où ça fuit

Mon raisonnement : si un point du signal contient de l'info sur le PIN, sa valeur devrait bouger d'une trace à l'autre. Si c'est juste du bruit, ça reste stable. Donc je calcule l'écart-type de chaque point sur les 9999 traces.

```python
import numpy as np, glob, os

fs = sorted(glob.glob('trace_*.npy'))
pins = np.array([os.path.basename(f)[6:10] for f in fs])
M = np.stack([np.load(f) for f in fs])     # 9999 x 100

print(M.std(axis=0)[:10].round(4))
```

```
[0.0541 0.0074 0.0076 0.0069 0.0077 0.0103 0.0068 0.0066 0.0059 0.0066]
```

Le point 0 est à 0.054 alors que les autres sont autour de 0.007, soit presque 8 fois plus. Il se passe clairement quelque chose là.

Je regarde quelles traces ont les plus grosses valeurs à cet endroit :

```python
s0 = M[:, 0]
for i in s0.argsort()[::-1][:10]:
    print(pins[i], round(s0[i], 5))
```

```
9194 0.43359
9330 0.43359
9009 0.42969
9232 0.42578
9200 0.42578
9355 0.42578
9412 0.42578
9748 0.42578
9166 0.42578
9268 0.42578
```

Elles commencent toutes par 9. Là j'ai compris : le premier chiffre du PIN se voit dans l'amplitude.

## Rendre ça systématique

Regarder les 10 plus grandes valeurs à la main ça passe pour le premier chiffre, mais ça ne tiendra pas pour les suivants. Il me faut un truc automatique.

L'idée : je regroupe les traces par chiffre candidat (celles qui commencent par 0, par 1, etc.) et je compare la moyenne de chaque groupe. Le bon chiffre devrait se démarquer des 9 autres. Et pour savoir à quel instant regarder, je cherche le point où ces 10 moyennes sont le plus dispersées :

```python
d = np.array([[int(c) for c in p] for p in pins])   # 9999 x 4

for k in range(4):
    scores = []
    for s in range(100):
        moyennes = [M[d[:, k] == v, s].mean() for v in range(10)]
        scores.append(np.var(moyennes))
    scores = np.array(scores)
    top = scores.argsort()[::-1][:3]
    print(f'chiffre {k} : points {top}, scores {scores[top].round(6)}')
```

```
chiffre 0 : points [37 57 76], scores [0.024735 0.01788  0.013664]
chiffre 1 : points [48 68 87], scores [0.000253 0.000186 0.000142]
chiffre 2 : points [26 25 59], scores [0.000007 0.000003 0.000002]
chiffre 3 : points [26 25  0], scores [0.000006 0.000005 0.000001]
```

Ça marche bien pour le premier chiffre (0.0247), déjà 100 fois moins pour le deuxième, et après c'est mort.

J'ai bloqué un moment dessus avant de comprendre, et en fait c'est logique : sur mes 9999 traces il n'y en a que 1000 qui ont le bon premier chiffre. Les 9000 autres se sont arrêtées avant même d'arriver au deuxième. Donc quand je cherche le deuxième chiffre sur tout le lot, mon signal est noyé sous 90 % de traces qui n'ont rien à dire.

La solution c'est donc de **filtrer au fur et à mesure**.

## L'attaque

Le principe :

1. Je cherche le 1er chiffre sur les 9999 traces
2. Je garde les 1000 qui commencent par ce chiffre, je cherche le 2e
3. Je garde les 100 qui restent, je cherche le 3e
4. Je garde les 10 qui restent, je cherche le 4e

```python
import numpy as np, glob, os

fs = sorted(glob.glob('trace_*.npy'))
pins = np.array([os.path.basename(f)[6:10] for f in fs])
M = np.stack([np.load(f) for f in fs])
d = np.array([[int(c) for c in p] for p in pins])

prefixe = ''
for k in range(4):
    # je garde que les traces compatibles avec ce que j'ai déjà trouvé
    masque = np.ones(len(pins), bool)
    for j, c in enumerate(prefixe):
        masque &= (d[:, j] == int(c))
    sub, subd = M[masque], d[masque]

    # où est le point de fuite pour cette position
    scores = np.array([
        np.var([sub[subd[:, k] == v, s].mean()
                for v in range(10) if (subd[:, k] == v).sum() > 0])
        for s in range(100)
    ])
    s = scores.argmax()

    # les moyennes par groupe à ce point
    moyennes = {v: sub[subd[:, k] == v, s].mean()
                for v in range(10) if (subd[:, k] == v).sum() > 0}
    # le bon chiffre c'est celui qui s'écarte le plus des autres
    mediane = np.median(list(moyennes.values()))
    meilleur = max(moyennes, key=lambda v: abs(moyennes[v] - mediane))

    print(f'position {k} | {masque.sum()} traces | point {s}')
    for v, m in sorted(moyennes.items()):
        marque = '  <--' if v == meilleur else ''
        print(f'   {v} : {m:+.4f}{marque}')

    prefixe += str(meilleur)

print(f'\nPIN = {prefixe}')
```

Résultat :

```
position 0 | 9999 traces | point 37
   0 : -0.1005
   1 : -0.0930
   2 : -0.0990
   3 : -0.0896
   4 : -0.0934
   5 : -0.0935
   6 : -0.0893
   7 : -0.0895
   8 : -0.0983
   9 : +0.4301  <--

position 1 | 1000 traces | point 48
   0 : -0.1138
   1 : -0.1068
   2 : -0.1073
   3 : -0.1037
   4 : +0.4192  <--
   5 : -0.1064
   6 : -0.1055
   7 : -0.1016
   8 : -0.1040
   9 : -0.1003

position 2 | 100 traces | point 59
   0 : -0.1168
   1 : -0.1090
   2 : -0.1164
   3 : -0.1121
   4 : -0.1145
   5 : -0.1090
   6 : +0.4164  <--
   7 : -0.1105
   8 : -0.1137
   9 : -0.1109

position 3 | 10 traces | point 85
   0 : -0.1445
   1 : -0.1406
   2 : -0.1445
   3 : -0.1445
   4 : -0.1406
   5 : -0.1484
   6 : +0.4180  <--
   7 : -0.1445
   8 : -0.1406
   9 : -0.1406

PIN = 9466
```

Je pensais devoir bricoler des seuils mais en fait non : à chaque étape le bon chiffre est à +0.42 et les 9 autres sont tous vers -0.11. C'est net.

Un truc que je trouve cool : les points de fuite sont à 37, 48, 59 puis 85. Les trois premiers sont espacés de 11 points pile. Ça correspond à la boucle du code, chaque tour prend le même temps. On voit littéralement les itérations dans le signal.

## Conclusion

**Flag : `FCSC{9466}`**

