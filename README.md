# Blender Autosave Backup

Customizable autosave location

![Autosave Add-on](/images/1.png)

Try it with "Save Now" or turn the autosave on or off with "Start Autosave"

![Autosave UI](/images/2.png)

# How to use

Download [Here](https://github.com/Zigatronz/Blender-ASB/releases) and install it in Blender at `Edit > Preferences > Add-ons > Install`

## Save Filename Format

Combine those as you desire
```
<TempDir>   = Temporary folder path
<ParentDir> = Parent path of saved blend if not this will be replace by temporary folder
<Filename>  = Blend filename without extension, 'Untitled' if not saved yet
<YYYY>      = 4 digits year
<MM>        = 2 digits month
<DD>        = 2 digits day
<hh>        = 2 digits hour
<mm>        = 2 digits minuit
<ss>        = 2 digits second
```

Like the default one `<ParentDir>\<Filename>\<Filename>-<YYYY>-<MM>-<DD>_<hh>-<mm>-<ss>.blend` and here the structure will be:

![Autosave structure 1](/images/3.png)

Another examples:

`<ParentDir>\<Filename>-<YYYY>-<MM>-<DD>_<hh>-<mm>-<ss>.blend`

or

`<TempDir>\<Filename>-<YYYY>-<MM>-<DD>_<hh>-<mm>-<ss>.blend`

which save at temporary folder instead

![Autosave structure 2](/images/4.png)

<br>

## Have a great day!

