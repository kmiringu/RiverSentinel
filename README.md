# RiverSentinel
RiverSentinel Business Case: From Pixel to Policy.

1. The Market Problem(Data Gap)
	- The inefficiency: Under the Nairobi Rivers Commission Special Planning Area declaration, the applicable buffer is 30-t0-60-meter as a riparian buffer zone. However, these agencies lack the field personnel to manually survey thousands of kilometers of riverbanks.
	- The Technical failure: Current government remote-sensing models rely on how resolution imagery that creates a "Blob Effect"(blending tightly packed homes together). This leads to a severe undercount (e.g. flagging only 118 structures a government blob-count vs when 700 as Pamoja Trust's manual ground count), leaving hundreds of vulnerable families completely invisible to disaster relief and town planners.

2. The Solution: RiverSentinel is an AI-powered spatial analysis analytics platform where Sentinel-2(10m, frequent revisit) drives the Random Forest layer for tracking encroachment trend over time; the 50cm imagery drives YOLOb8-seg for accurate one-time-or-periodic building counts.

	Business deliverables
- This standardized Operational Intelligence Packet tool outputs 3 concrete business deliverables:
1. Prioritised Triage Action Queue:
	 - High/Med/Low Risk (CSV) - Sorted buildings by its exact proximity to the river centerline
	 - Centroid Coordinates - Exact GPS coordinates for field confirmation

2. Human & Logistical Exposure Dashboard
	 - Dynamic Population estimation - automatically multiply structure count by the informal settlement average density.
	 - Infrastructure Flags - identify unusually large geometric shapes within the zone and flag as critical assets.

3. Spatiotemporal Drift Velocity Log
	 - Chronological Timeline - line graph showing physical settlements.
	 - Rapid-Growth Hotspots 



    Nairobi built-up area change detection & riparian encroachment monitor. <br>

			MORINGA SCHOOL
                CAPSTONE PROJECT - Made with Love.
