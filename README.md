#Game Development Shelf

This is a series of tools geared towards assisting Houdini users with a variety of tasks for game development.

The instructions for getting this installed is pretty painless. It's really just a matter of copying the files, activating the shelf, and then saving a desktop so it's easy to access.

##Instructions
Copy the contents of this folder into the following folders depending on your operating system:

Windows

    C:\Users\[username]\Documents\houdini[ver#]

OSX

    /Users/[username]/Library/Preferences/houdini/[ver#]

Be sure to merge as needed! If you're copying and not cloning, the files shouldn't overwrite anything that doesn't involve the toolset.

##How to use the included desktops
01. At the top menu, click Windows -> Desktop
02. Select any of the GameDev desktops for your role!

It's not recommended to modify the layout of any of the GameDev desktops. If you pull from the SideFX repo, it's possible a conflict will occur. Instead, do a "save as" operation. Alternatively, you can also select one of the other shelves that aren't for game development, activate the shelf, and then save that!

##Activating the Shelf
01. Looking towards the very right of one of the shelves, click the little triangle pointing downwards
02. Click Shelf Sets
03. Click Game Development

##Saving its location
01. At the top menu, click Windows
02. Desktop
03. Save Current Desktop

Keep in mind, that will override the "Build" desktop. If you want to create a new desktop, click "Save Current Desktop As...".

##Setting the default desktop (if using a custom desktop)
01. At the top menu, click Edit -> Preferences -> General User Interface (alternatively: `ctrl+,` or `cmd+,`)
02. At the "Startup in Desktop" field, select the desktop you would like to use
03. Accept!

##Having the terminal automatically source Houdini (OS X)
In your ~/.bash_profile, add the following lines:

    ##Houdini Environment Setup
    cd /Library/Frameworks/Houdini.framework/Versions/Current/Resources
    source houdini_setup
    cd -

That will change the directory to the latest version of Houdini, source the houdini_setup.source file, and then change the directory back to where it was initially.
