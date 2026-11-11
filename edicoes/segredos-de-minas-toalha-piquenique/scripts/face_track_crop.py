"""Face track for small faces: detect on a 2x upscaled crop (x 240-840, y 400-1200)."""
import sys, json, cv2, mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision
S=sys.argv[1]; video=sys.argv[2]; out=sys.argv[3]
import os
X0,Y0,X1,Y1=[int(v) for v in os.environ.get("FACE_CROP","240,400,840,1200").split(",")]; K=2.0
opts=vision.FaceLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path=S+"/models/face_landmarker.task"),running_mode=vision.RunningMode.VIDEO,num_faces=1)
lm=vision.FaceLandmarker.create_from_options(opts)
cap=cv2.VideoCapture(video); fps=cap.get(cv2.CAP_PROP_FPS); i=0; res=[]
while True:
    ok,fr=cap.read()
    if not ok: break
    if i%3==0:
        crop=cv2.resize(fr[Y0:Y1,X0:X1],None,fx=K,fy=K,interpolation=cv2.INTER_CUBIC)
        h,w=crop.shape[:2]
        r=lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(crop,cv2.COLOR_BGR2RGB)),int(i*1000/fps))
        if r.face_landmarks:
            L=r.face_landmarks[0]
            f=lambda p:[X0+p.x*w/K, Y0+p.y*h/K]
            xs=[X0+p.x*w/K for p in L]
            res.append({"t":i/fps,"chin":f(L[152]),"top":f(L[10]),"nose":f(L[1]),"xmin":min(xs),"xmax":max(xs)})
        else: res.append({"t":i/fps,"chin":None})
    i+=1
json.dump({"fps":fps,"frames":i,"track":res},open(out,"w"))
print("frames",i,"detected",sum(1 for r in res if r["chin"]))
