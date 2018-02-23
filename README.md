# Game Development Toolset

This is a series of tools geared towards assisting Houdini users with a variety of tasks for game development. The older version of this repository focused on just the shelf. Now this is an all-inclusive toolset that spans the shelf, digital assets, custom desktops and scripts.

If you'd like more information, please check out the overview page, which contains tutorials for several of the provided tools. [https://www.sidefx.com/tutorials/game-development-toolset-overview/](https://www.sidefx.com/tutorials/game-development-toolset-overview/)

NOTE: This is in-progress. Please file an [Issue](https://github.com/sideeffects/GameDevelopmentToolset/issues) if something doesn't seem quite right! Guidelines can be found [here](https://github.com/sideeffects/GameDevelopmentToolset/wiki/How-to-contribute!).

Also, if you forked the respository and suddenly it stopped pulling, that's due to the link changing from [https://github.com/sideeffects/GameDevelopmentShelf/](https://github.com/sideeffects/GameDevelopmentShelf/) to [https://github.com/sideeffects/GameDevelopmentToolset/](https://github.com/sideeffects/GameDevelopmentToolset/). Github appears to forward traffic to the new link, but here's a little FYI just incase.

# Installation



## Instructions - Method 1
Download the repository using the green Clone or Download Button and unzip contents into the following folders depending on your operating system:

Windows

    C:\Users\[username]\Documents\houdini[ver#]

OSX

    /Users/[username]/Library/Preferences/houdini/[ver#]

Linux

    ~/houdini[ver#]

Be sure to merge as needed! If you're copying and not cloning, the files shouldn't overwrite anything that doesn't involve the toolset.

## Instructions - Method 2
Download the repository using the green Clone or Download Button and unzip contents into the folder of your choosing

Edit the houdini.env file found at the topmost directory 

Modify the line HOUDINI_PATH = C:\PATH\TO\YOUR\DIRECTORY;&

Into something like HOUDINI_PATH = C:\Users\Luiz\Documents\GameDevelopmentToolset;&

Copy the houdini.env file into the following folders depending on your operating system:

Windows

    C:\Users\[username]\Documents\houdini[ver#]

OSX

    /Users/[username]/Library/Preferences/houdini/[ver#]

Linux

    ~/houdini[ver#]

# What's Changed?
Hi, my name is Luiz Kruel and I have taken over the github from Steven B. who is now working in production. A few of the SideFX TAs (TDs) will also be contributing example files and tools.

We haven't done a lot in this Github in a while, but we are changing that. The original thought was that new tools would go straight into the build and the Github would eventually be phased out.
But we saw a lot of value in having this experimental testbed for tools, so we will continue to develop our tools live and as they mature they will move into the main Houdini Build.

## Live Development
We're actively working on building up the Houdini 16.0 branch of the toolset to match what's curently in the build.
Currently we are moving tools over as bugs are indentified and fixed, and are placed here until they get added into the main Houdini build.
We will also develop new tools moving forward using GitHub as our version control, so in the near future the 16.0 branch will become the default branch

## Expanded HDAs
All of the HDAs are now using the new expanded format that was introduced in H16. This allows better diffing of the tools so you can see what our changes are doing and choose to integrate them back into your production.

## Example Files
Instead of tying the examples as HDAs, we will be generating separate hip files that show how the tools should work in context

## Branched Development
The *Development* branch is where we'll be working from. This is where the latest and greatest will live

Once an HDA is deemed ready, we will move it over to the Houdini XX branch where it will be more easily discovered by the population at large


