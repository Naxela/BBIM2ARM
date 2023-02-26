# BBIM2ARM

![Header](https://github.com/Naxela/BBIM2ARM/raw/main/IFC2ARM_Screen.png)

BIM2ARM is an addon for Blender that seeks merge the constructive powers of BlenderBIM with the visual powers of Armory3D to open up for easy and interactive web experiences. The addon is mainly intended for usage in the AEC industry for visualizing and communicating designs.

What does it actually do?
- It allows you to deploy your IFC files straight to the web as HTML5 files, or executables (for instance windows .exe files) that the client can view straight away without the need to download any dependencies.

How easy is it to use?
It only takes 4-5 steps from importing an IFC to have a result:
1. Select Import your IFC file (It imports the IFC using BlenderBIM)
2. Select Clean the IFC file (It makes it ready for Armory3D)
3. Select Configure Armory (Setup graphics, resolution, camera, property inspection, and more)
4. Select Start (Quickly preview what it's going to look like)
5. Select your preferred platform - HTML5 for a web experience, or Binary for an executable.

![Animation](https://github.com/Naxela/BBIM2ARM/raw/main/BIM2ARM_Animation.gif) 

Features:
- Easily transform your IFC to something your client can view 
- Clean your IFC files of unnecessary clutter
- Fly and walk through your 3D models with easy
- Simulate shadows based on location and time
- Convert your IFC materials into PBR materials


What's the catch?
- While it's open-source and free, it's also new. There's bound to be bugs, and it's only me working on it. I'd appreciate it if you can list any bugs you find so I can squish them


Roadmap:
- Place PDF at cursor/empty? Auto-detect DPI? Sections, fasade, etc.
- Support for better classification overview?
- Integrated HTML5 Preloading (div w. gif overlay, integrated call to hide on init?)
- 4D, 5D, 6D, 7D support?
- Physics setup with walkable players
- Expanded/integrated material replacement database
- PDF Plan alignment tool:
-- Python: PDF to JPG, pdf2image library => High vs. Low DPI => Use grids for alignment?
- Placeholder class replacement
- Better support for BIM properties
- Support for viewing IFC Schedules
- Expanded model tree sorting (Hierarchy layouts)
- BCF highlighting and focus areas
- Geolocation support for realworld mobile device location and orientation
- 2D Annotation support
- Performance improvements / Adaptive LOD scaling / IFC Class based dynamic occlusion
- Dynamic weather support
- Automated lightmapping support
- IFC Class Toggle
- Revit light placement w. IES support
- Additional custom data input (ie. clickable image wall detailing, custom spreadsheets)

![Animation](https://github.com/Naxela/BBIM2ARM/raw/main/Screenshot.jpg)
