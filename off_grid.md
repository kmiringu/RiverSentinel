To understand the exact mathematical data requirements of deep learning.

We break down the dataset sizing, target scale of individual structure footprints and our tool choice.

1. Dataset Dimensions and Scale
   How many images are in the training set?
	- Our target training database should contain a minimum 200-500 distinct image tiles(sliced cleanly at a resolution of 640 by 640 pixels)

   #Data Splitting.
	- we must capture the 12-month climate cycle, we split the dataset roughly 50/50: 
	a) 150 - 250 tiles from the dry season.
	b) 150 - 250 tiles from the wet season.

   - Example; a 350 tile training set using a standard 70/15/15 ml split. we have 245 tiles for training, 52 tiles for validation and 53 tiles for baseline testing.

2. How many individual structures need a polygon drawn around them?
	- for YOLOv8-seg to effectively learn the layout of an informal settlement without overfitting, it requires exposure to a min 3,000 to 5,000 individual building instances.
	- Informal settlements are densely packed, a single 640 by 640 pixel satellite tile can easily contain between 15 to 45 individual shacks
	- The high density is an advantage in that by acquiring just 350 high-resolution images, we capture the thousands of individual structural footprints necessary for deep learning.

3. Tooling annotation
	- Since we are using the Microsoft Global Building Footprints to pre-populate the layout, we use annotation tools for rather than drawing 5,000 structures by hand.
	a) data validation
	b) manual cleaning
	c) quality control


	CHOICE OF TOOLS TRADEOFF
    ROBOFLOW
	- Free tool and understands the YOLOv8-seg data structure.
	- It includes a 'smart polygon" AI Magic Wand which one can hover over a shack in a satellite tile, click once, and the underlying AI instantly traces the edges of the corrugated iron roof, generating a multi-point polygon.
	- it exports unifiedly into data.yaml ready for training.

    CVAT(Computer Vision Annotation Tool)
	- Runs on Linux natively only. 
	- It can be hosted locally via Docker completely offline, keeping massive, heavy GeoTIFF imagery processing fast and local.
	- It has an excellent inter-annotator verification queue; i.e. if 3 members split the validation work, we can set a rule where member 3 must digitally "approve" the polygons drawn by the previous members to ensure absolute geometric consistency before running the model.

    LABELME(Native Baseline)
	- Open-source, local desktop application.
	- Drawback: it outputs annotations as individual .json or .xml meaning the last member would have to manually write a script to transform these coordinate matrices into the normalized [class_id x1 y1 x2 y2] syntax that YOLO requires.
	- Adds unnecessary friction.

Recommended: ROBOFLOW


    NB:
	- If and when we trim a large orthomosaic into 640 by 640 chips, builings sitting on a tile boundary get cut in half.
	- Our model could miss or counts the same building twice.
	
    Solution:
	- Overlapping tiles plus a non-max suppresion or deduplication pass on the stitched-together output.
	- This merges a building spanning two tiles into one detection.
