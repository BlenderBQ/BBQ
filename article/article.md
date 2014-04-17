# BlenderBQ : interface vocale et gestuelle pour Blender

# L'architecture de l'application

Notre application est divisée en deux parties : un serveur qui récupère et
traite les commandes utilisateurs, et un client qui se charge de les traiter dans Blender.

## Le serveur

Dans un premier temps, le serveur va démarrer l'écoute d'événements du
LeapMotion, ainsi que la pipeline de reconnaissance vocale (dont les
fonctionnements sont détaillés plus loin).

Celui-ci tourne sur Python 2.7, car l'API LeapMotion [n'est pas][1] (à l'écriture
de cette article) compatible avec les versions suivantes de Python (3.3 par
exemple). L'architecture client-serveur est tout ce qu'il y a de plus standard :
le serveur va envoyer des commandes en fonction des entrées LeapMotion /
reconnaissance vocale, via une simple connexion socket. Nous avons tout
d'abord utilisé des socket UNIX par souci de performance des sockets TCP, mais
il s'avère que la différence n'est plus tant notable.

[1]: https://developer.leapmotion.com/documentation/Leap_SDK_Release_Notes.html#supported-compilers-and-runtimes "Supported compilers and runtime"

## Le client

Le scripting de Blender est également fait en Python, mais contrairement au
serveur, celui-ci utilise une version modifiée de Python 3, adaptée à son
usage. C'est pourquoi nous avons utilisé des sockets relativement *bas-niveau*, plutôt que des systèmes de communication RPC ou avec un [Manager][2], qui utilise
Pickle, donc incompatible entre versions de Python.

[2]: https://docs.python.org/3.3/library/multiprocessing.html#managers "Python 3.3 Managers"

En ce qui concerne le contrôle de Blender, beaucoup d'obstacles ont dû être surmontés :

Blender bloque dès lancements d'un script, et ce jusqu'à ce que celui-ci se termine. Cependant, nous devions absolument maintenir l'écoute sur le serveur d'entrées. Nous avons donc utilisé le concept d'[opérateurs modaux][3] mis à disposition par Blender.

[3]: http://www.blender.org/documentation/blender_python_api_2_70_release/bpy.types.Operator.html "Opérateurs modaux Blender"

Ces opérateurs fonctionnent en effectuant certains *callbacks* particuliers, au
fur et à mesure de l'utilisation de l'opérateur. Ceux-ci bloquent le
fonctionnement de Blender, et donc nécessitaient un parallélisme pour récupérer
les commandes du serveur. Malheureusement, Blender [n'est pas thread-safe][4], ce
qui nous a obligé à effectuer uniquement des opérations non-bloquantes lors de
la récupération des commandes, ainsi que la gestion des paquets expirés ou
redondants.

[4]: http://www.blender.org/documentation/blender_python_api_2_70_release/info_gotcha.html#strange-errors-using-threading-module

Ainsi, à chaque réception de commande, un ordre est activé et un affichage se
met en place pour changer les objets ("mesh") de Blender. Notez que le système
de coordonnées de Blender et celui du LeapMotion sont très différents, ce qui
induit une conversion obligatoire des valeurs de coordonnées. D'abord à cause
de l'échelle, mais aussi à cause de l'orientation des axes et de la différence
entre coordonnées absolues et relatives.

# Commande vocale

## La chaîne de traitement

La commande vocale est basée sur l'utilisation de PocketSphinx (CMUSphinx),
intégré via une pipeline GStreamer, et disponible à travers une librairie
Python. Nous avons passé beaucoup de temps à comprendre le fonctionnement de la
pipeline, et où nous nous placions dans la chaîne d'information vocale. Finalement, nous avons défini un corpus de mots simples correspondant à des
commandes, et avons construit le dictionnaires et le modèle acoustique à partir
de l'outil [lmtool][5] de CMUSphinx.

[5]: http://www.speech.cs.cmu.edu/tools/lmtool-new.html

## Commandes implémentées

Le dictionnaire est constitué de mots courts et très différents les uns des autres afin de rendre leur reconnaissance plus fiable. Un premier groupe de commandes (ˋaboveˋ, ˋright`, ˋcameraˋ, etc) permet de contrôler la vue, tandis que le second groupe (`objectˋ, ˋpotteryˋ, ˋpaintˋ) sert à passer d'un mode à un autre.

Il est facile d'ajouter des commandes supplémentaires puisqu'il suffit de les insérer dans le dictionnaire puis de les faire correspondre à l'appel correspondant dans l'API Blender.

# La grammaire gestuelle

Au cours du temps, le Leap Motion envoie régulièrement des "frames", qui contiennent tout ce qu'il détecte. Ces frames comprennent le nombre de mains détectées et leur position en 3 dimensions, ainsi que le nombre de doigts visibles pour chaque main, ainsi que leur position. La fréquence d'envoi des frames est élevée : environ 20 frames sont envoyées par seconde. Cependant, cette fréquence peut varier selon les ressources disponibles, l'activité générale, et d'autres facteurs. À chaque réception d'une de ces frames, notre serveur analyse le mouvement des mains de l'utilisateur. Ceci est réalisé principalement par mémorisation des informations clé à chaque étape, afin d'en analyser l'évolution au cours du temps.

En 24 heures, nous avons implémenté quatre gestes :

- Le geste `grab` permet d'attraper l'objet, de le déplacer dans l'espace et éventuellement de le faire pivoter selon chaque axe.
- De manière complémentaire, le geste `scale` permet d'agrandir ou rétrécir l'objet en mimant un étirement avec les deux mains.
- Un balayement de la main (geste `swipe`) permet, à la manière d'un potier, de mettre en rotation un objet.
- Enfin, le geste `touch` permet, en pointant le doigt dans la direction souhaitée, de sculpter l'objet de manière très intuitive.

# Première place au hackathon Fhacktory

L'application BBQ a été réalisée en 24 heures pendant le hackathon Fhacktory de Mars 2014 et a pris la première place.

Merlin Nimier-David, Jean-Marie Commets, Pierre Turpin, Arthur Gustave Monod, Alin Dicu (Fhacktory)
