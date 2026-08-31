#!/usr/bin/env python3
import sys
import glob
import os
import numpy as np


def charger(dossier):
    fs = sorted(glob.glob(os.path.join(dossier, 'trace_*.npy')))
    if not fs:
        sys.exit(f"Aucune trace trouvee dans {dossier}")
    pins = np.array([os.path.basename(f)[6:10] for f in fs])
    M = np.stack([np.load(f) for f in fs])
    return pins, M


def point_de_fuite(sub, subd, k):
    scores = np.array([
        np.var([sub[subd[:, k] == v, s].mean()
                for v in range(10) if (subd[:, k] == v).sum() > 0])
        for s in range(sub.shape[1])
    ])
    return scores.argmax()


def attaque(pins, M, verbeux=True):
    d = np.array([[int(c) for c in p] for p in pins])
    prefixe = ''

    for k in range(4):
        masque = np.ones(len(pins), bool)
        for j, c in enumerate(prefixe):
            masque &= (d[:, j] == int(c))
        sub, subd = M[masque], d[masque]

        s = point_de_fuite(sub, subd, k)

        moyennes = {v: sub[subd[:, k] == v, s].mean()
                    for v in range(10) if (subd[:, k] == v).sum() > 0}
        mediane = np.median(list(moyennes.values()))
        meilleur = max(moyennes, key=lambda v: abs(moyennes[v] - mediane))

        if verbeux:
            print(f'position {k} | {masque.sum():4d} traces | echantillon {s}')
            for v, m in sorted(moyennes.items()):
                marque = '  <--' if v == meilleur else ''
                print(f'   {v} : {m:+.4f}{marque}')
            print()

        prefixe += str(meilleur)

    return prefixe


if __name__ == '__main__':
    dossier = sys.argv[1] if len(sys.argv) > 1 else 'traces'
    pins, M = charger(dossier)
    print(f'{len(pins)} traces de {M.shape[1]} echantillons\n')

    pin = attaque(pins, M)
    print(f'PIN  = {pin}')
    print(f'FLAG = FCSC{{{pin}}}')
