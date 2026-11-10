import sys, json, cv2, numpy as np, mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision
S=sys.argv[1]; video=sys.argv[2]; out=sys.argv[3]
opts=vision.FaceLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path=S+"/models/face_landmarker.task"),running_mode=vision.RunningMode.VIDEO,num_faces=1)
lm=vision.FaceLandmarker.create_from_options(opts)
cap=cv2.VideoCapture(video); fps=cap.get(cv2.CAP_PROP_FPS); i=0; res=[]
while True:
    ok,fr=cap.read()
    if not ok: break
    if i%3==0:
        h,w=fr.shape[:2]
        small=cv2.resize(fr,(w//2,h//2))
        img=mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(small,cv2.COLOR_BGR2RGB))
        r=lm.detect_for_video(img,int(i*1000/fps))
        if r.face_landmarks:
            L=r.face_landmarks[0]
            chin=L[152]; top=L[10]; nose=L[1]
            xs=[p.x for p in L]; 
            res.append({"t":i/fps,"chin":[chin.x*w,chin.y*h],"top":[top.x*w,top.y*h],"nose":[nose.x*w,nose.y*h],"xmin":min(xs)*w,"xmax":max(xs)*w})
        else: res.append({"t":i/fps,"chin":None})
    i+=1
json.dump({"fps":fps,"frames":i,"track":res},open(out,"w"))
print("frames",i,"fps",fps,"detected",sum(1 for r in res if r["chin"]))
