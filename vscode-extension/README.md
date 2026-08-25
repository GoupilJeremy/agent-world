# Agent World pour VS Code

Cette extension implémente **US-011 à US-013** : elle ajoute Agent World à
l’Activity Bar, charge les agents depuis l’API Flask, suit le thème de l’éditeur
et ouvre les fichiers générés avec les API natives de VS Code.

## Fonctionnalités

- conteneur **Agent World** dans l’Activity Bar ;
- vue **Agents** avec chargement, liste, état vide et erreur actionnable ;
- actualisation depuis la barre de titre de la vue ou la palette de commandes ;
- dashboard récapitulatif avec la commande `Agent World: Ouvrir le dashboard` ;
- détail d’un agent au clic sur son entrée dans l’arborescence ;
- adaptation automatique aux couleurs natives du thème VS Code ;
- ouverture sécurisée d’un fichier généré via le sélecteur natif de VS Code.

## Lancer en développement

1. Démarrez le backend depuis la racine du dépôt avec `python run.py`.
2. Ouvrez le dossier `vscode-extension/` dans VS Code.
3. Appuyez sur `F5`, puis choisissez **Extension Development Host** si VS Code le
   demande.
4. Dans la nouvelle fenêtre, ouvrez l’icône Agent World dans l’Activity Bar.

L’extension est écrite en JavaScript CommonJS et ne nécessite ni compilation ni
installation de dépendances pour s’exécuter.

## Configuration

Les réglages sont accessibles via **Préférences > Paramètres > Agent World** :

- `agentWorld.apiUrl` : URL du backend, par défaut
  `http://127.0.0.1:5000`. Ce réglage est limité à la machine afin qu’un dépôt
  ouvert ne puisse pas imposer un endpoint ;
- `agentWorld.requestTimeoutMs` : délai maximal d’une requête, par défaut
  `5000` ms ;
- `agentWorld.openFile.location` : groupe d’éditeur cible, `active` par défaut
  ou `beside` pour ouvrir à côté.

La liste est récupérée sous `{agentWorld.apiUrl}/api/agents`. Un éventuel préfixe
de chemin dans `agentWorld.apiUrl` est conservé. Le délai configuré couvre toute
la requête, y compris la résolution DNS, la connexion et la lecture de la réponse.
Toute modification de l’URL ou du délai actualise automatiquement la vue et le
dashboard ouvert ; l’emplacement choisi s’applique à la prochaine ouverture.

## Ouvrir un fichier généré

Utilisez la commande `Agent World: Ouvrir un fichier généré`, depuis la palette
ou l’icône de dossier dans la vue Agents. Le sélecteur natif permet de choisir un
fichier ; l’extension transmet directement l’URI sélectionnée à
`workspace.openTextDocument`, puis l’affiche avec `window.showTextDocument`.

Un appel programmatique peut proposer un chemin relatif, un chemin absolu ou une
URI. Il est accepté uniquement dans un workspace approuvé et ne sert que de
présélection : l’utilisateur doit toujours confirmer le fichier dans le picker.
Les relatifs sont résolus contre le workspace de l’éditeur actif ; en multi-root
sans éditeur actif, VS Code demande explicitement la racine à utiliser. Les chemins
vides, NUL, traversals, schémas hostiles et sorties de racine sont refusés.

Avant l’ouverture, `workspace.fs.stat` doit confirmer que l’URI désigne un fichier.
Pour les workspaces locaux, les chemins canoniques de la racine et du fichier sont
comparés afin de bloquer aussi les liens symboliques qui sortent du workspace. Pour
un fournisseur de fichiers distant, VS Code ne fournit pas de primitive `realpath` :
une entrée programmatique doit donc être une URI workspace créée par VS Code et les
liens symboliques signalés par le fournisseur sont refusés. Le picker et le contrôle
de racine restent obligatoires.

La commande n’est reliée à aucun chemin provenant de l’API ou d’une webview. Une
annulation ferme simplement le sélecteur et une erreur d’ouverture est présentée
dans une notification VS Code. Dans un workspace non approuvé, la consultation des
agents reste disponible mais l’ouverture programmatique de fichiers est désactivée.

## Tests

Node.js 18 ou plus récent est requis :

```shell
npm test
npm run check
```

Les tests utilisent le runner intégré de Node et des transports factices : ils
n’effectuent aucun appel réseau.

## Sécurité des webviews

Les webviews du dashboard et du détail sont statiques : JavaScript y est désactivé,
les ressources locales sont interdites, la CSP utilise `default-src 'none'`, et les
styles intégrés sont autorisés uniquement avec un nonce aléatoire. Toutes les valeurs
provenant de l’API sont échappées avant leur insertion dans le HTML.
