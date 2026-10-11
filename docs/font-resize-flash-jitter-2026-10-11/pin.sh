D=B0E25998-5905-45F9-A491-C81C1F269684
DATA=$(xcrun simctl get_app_container $D com.natebunnyfield.crosspoint.x3 data)
python3 -c "import json,sys;p=sys.argv[1]+'/Documents/.crosspoint/state.json';d=json.load(open(p));d['readerActivityLoadCount']=0;json.dump(d,open(p,'w'));print(d.get('openEpubPath'))" "$DATA"
