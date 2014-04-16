# L'architecture de l'application

Notre application est divisée en deux parties: un serveur qui récupère et
traite les commandes utilisateurs, et un client qui se charge de traiter en
conséquence sur Blender.

## Le serveur

Dans un premier temps, le serveur va démarrer l'écoute d'événements du
LeapMotion, ainsi que la pipeline de reconnaissance vocale (dont les
fonctionnements sont détaillés plus loin).

Celui-ci tourne sur Python 2.7, car l'API [LeapMotion n'est pas (à l'écriture
de cette article)][1] compatible avec les versions suivantes de Python (3.3 par
exemple). L'architecture client-serveur est tout ce qu'il y a de plus standard :
le serveur va envoyer des commandes en fonction des entrées LeapMotion /
reconnaissance vocale, via une simple connexion socket. Nous avons tout
d'abord utilisé des socket UNIX par souci de performance des sockets TCP, mais
au final la différence n'est plus tant notable.

[1]: https://developer.leapmotion.com/documentation/Leap_SDK_Release_Notes.html#supported-compilers-and-runtimes "Supported compilers and runtime"

## Le client

Le scripting de Blender est fait en Python aussi, mais contrairement au
serveur, celui-ci utilise une version modifiée de Python 3, adaptée à son
usage. C'est pourquoi nous avons utilisé des sockets plutôt "bas-niveau", plutôt
que des systèmes de communication RPC ou avec un [Manager][2], qui utilise
Pickle, donc incompatible entre versions de Python.

[2]: https://docs.python.org/3.3/library/multiprocessing.html#managers "Python 3.3 Managers"

En ce qui concerne le contrôle de Blender, beaucoup d'obstacles ont dû être surmontés :

Blender bloque au lancement d'un script, jusqu'à ce que celui-ci se termine,
alors qu'on devait absolument maintenir l'écoute sur le serveur d'entrées. Nous
avons donc utilisé le concept d'[opérateurs modaux][3] existant dans Blender.

[3]: http://www.blender.org/documentation/blender_python_api_2_70_release/bpy.types.Operator.html "Opérateurs modaux Blender"

Ces opérateurs fonctionnent en effectuant certains *callbacks* particuliers, au
fur et à mesure de l'utilisation de l'opérateur. Ceux-ci bloquent le
fonctionnement de Blender, et donc nécessitaient un parallélisme pour récupérer
les commandes du serveur. Malheureusement, Blender [n'est pas thread-safe][4], ce
qui nous a obligé d'effectuer uniquement des opérations non-bloquantes lors de
la récupération des commandes, ainsi que la gestion des paquets expirés ou
redondants.

[4]: http://www.blender.org/documentation/blender_python_api_2_70_release/info_gotcha.html#strange-errors-using-threading-module

Ainsi, à chaque réception de commande, un ordre est activé et un affichage se
met en place pour changer les objets ("mesh") de Blender. Notez que le système
de coordonnées de Blender et celui du LeapMotion sont très différents, ce qui
induit une conversion obligatoire des valeurs de coordonnées. D'abord à cause
de l'échelle, mais aussi à cause de l'orientation des axes et de la différence
entre coordonnées absolues et relatives.

# La chaîne de commande vocale

La commande vocale est basée sur l'utilisation de PocketSphinx (CMUSphinx),
intégré via une pipeline GStreamer, et disponible à travers une librairie
Python. Nous avons passé beaucoup de temps à comprendre le fonctionnement de la
pipeline, et où nous nous placions dans la chaîne d'information vocale. Au
final, nous avons défini un corpus de mots simples correspondant à des
commandes, et avons construit le dictionnaires et le modèle acoustique à partir
de l'outil [lmtool][5] de CMUSphinx.

[5]: http://www.speech.cs.cmu.edu/tools/lmtool-new.html

# La grammaire de geste

Au fur et à mesure du temps, le LeapMotion envoie en continu un "frame", qui
contient tout ce qu'il détecte. Ce frame comprend le nombre de mains détectées
et leur position en 3 dimensions, ainsi que le nombre de doigts visibles de
chaque main et leur position. Il est envoyé très souvent, environ 20 fois par
seconde (cette fréquence peut varier selon les ressources disponibles,
l'activité générale, et d'autres facteurs). À chaque réception d'un de ces
frames, notre serveur analyse le mouvement des mains de l'utilisateur. Ceci est
fait en mémorisant les informations qui nous intéressent d'un frame à un autre,
pour en voir l'évolution au cours du temps.

## Le "Grab" pour attraper un objet

Le premier geste que nous avons développé pour notre application est le Grab.
L'idée est de reconnaître quand un utilisateur décide d'attraper l'objet
courant pour lui permettre de relier le déplacement de sa main avec celui de
l'objet. Pour ce faire, nous avons commencé par filtrer le nombre de doigts. Ce
filtrage reconnait les informations parasites (changements brutaux) et filtre
le bruit engendré. Puis un filtre passe bas fait une moyenne pondérée de sorte
à avoir une courbe plus représentative du nombre de doigts au cours du temps.
C'est en analysant cette courbe (et en particulier sa dérivée) que l'on peut
détecter la fermeture (début du Grab) et l'ouverture de la main (fin du Grab).

## Le "Scale" pour agrandir ou rétrécir un objet

TODO Écrire comment fonctionne le scale

## Le "Swipe" pour faire tourner un objet

TODO Écrire comment fonctionne le swipe

## Le "Calm down" pour stopper la rotation

TODO Écrire comment fonctionne le calm down

# Les différents modes et leur utilité

## Le mode object

Le mode d'ouverture par défaut de notre application est le mode object. Il
permet le déplacement d'un objet suite à l'action de Grab, et la mise à
l'échelle avec le Scale.

## Le mode poterie

Dans ce mode, il est possible de faire tourner un objet (avec le Swipe) plus ou moins vite autour de son axe vertical. De plus, le mouvement du doigt permet de sculpter l'objet de deux façons différentes: soit en retrait (qui enlève de la matière à l'objet), soit en ajout de matière. On peut voir l'effet du déplacement de son doigt grâce à une petite sphère qui indique où se trouve le doigt.

## Le mode paint

De plus, il est possible de changer la couleur globale de l'objet en choisissant la couleur grâce à la position de la main (en trois dimensions reliées au Rouge, Vert et au Bleu).

## Le changement d'angle de vues

Dans tous les modes, il est possible de changer d'angle de vue, sur les côtés (left et right) du dessus (*above* et under), ou encore selon la vue de la caméra (camera).
