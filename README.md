#Game Development Shelf

This is a series of tools geared towards assisting Houdini users with a variety of tasks for game development. 

Windows

    C:\Users\[username]\Documents\houdini[ver#]\toolbar

OSX

    /Users/[username]/Library/Preferences/houdini/[ver#]/toolbar

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
