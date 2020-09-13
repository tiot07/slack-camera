# coding: utf-8
from slackbot.bot import respond_to     # @botname: で反応するデコーダ
from slackbot.bot import listen_to      # チャネル内発言で反応するデコーダ
from slackbot.bot import default_reply  # 該当する応答がない場合に反応するデコーダ
import cv2
import requests
import shlex
import configparser
import subprocess as sb
import sys
import os
import time
import datetime
count = 0

#slackへ送信する関数
def slack(filename,title,status):
  param = {
  'token':"token", 
  'channels':"channels",
  'filename':"filename",
  'initial_comment': status,
  'title': title
  }
  files = {'file': open(filename, 'rb')}
  requests.post(url="https://slack.com/api/files.upload",params=param, files=files)

#３つの画像から差分を計算
def check_image(img1, img2, img3):
    # グレイスケール画像に変換
    gray1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)
    gray3 = cv2.cvtColor(img3, cv2.COLOR_RGB2GRAY)
    # 絶対差分を調べる
    diff1 = cv2.absdiff(gray1, gray2)
    diff2 = cv2.absdiff(gray2, gray3)
    # 論理積を調べる
    diff_and = cv2.bitwise_and(diff1, diff2)
    # 白黒二値化
    _, diff_wb = cv2.threshold(diff_and, 30, 255, cv2.THRESH_BINARY)
    # ノイズの除去
    diff = cv2.medianBlur(diff_wb, 5)
    return diff

#カメラから画像取得
def get_image(cam):
    img = cam.read()[1]
    img = cv2.resize(img, (1280, 720))
    return img

#動画を撮影し、mp4に変換した後slackへ送信
def video():
    global count
    cap = cv2.VideoCapture(0)
    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('output.avi',fourcc, 30.0, (640,480))
    start=time.time()
    while(cap.isOpened()):
        ret, frame = cap.read()
        if ret==True and time.time()-start<60:
            # write the flipped frame
            out.write(frame)
        else:
            break
    cap.release()
    out.release()
    count=2
    cmd="ffmpeg -y -i output.avi output.mp4"
    sb.call(cmd.split())
    slack("output.mp4","output.mp4","output.mp4")

#動きを検知したら動画をslackへ送信し、1時間後に検知開始
@respond_to('video')
def mention_func(message):
    message.reply('動体検知開始') # メンション
    global count
    # カメラのキャプチャを開始
    cam = cv2.VideoCapture(0)
    # フレーム、時間の初期化 --- (*1)
    img1 = img2 = img3 = get_image(cam)
    th = 100
    while True:
        # Enterキーが押されたら終了
        #if cv2.waitKey(1) == 13: break
        if(count==0):
            # 差分を調べる --- (*2)
            diff = check_image(img1, img2, img3)
            # 差分がthの値以上なら動きがあったと判定 --- (*3)
            cnt = cv2.countNonZero(diff)
            img1, img2, img3 = (img2, img3, get_image(cam))
            if cnt > th:
                print("カメラに動きを検出")
                cv2.imwrite("video.jpg", img3)
                slack("video.jpg","カメラに動きを検出","カメラに動きを検出")
                cam.release()
                count=1
                video()
                time.sleep(3600)
                while count==1:
                    time.sleep(20)
        elif(count==1):
            cam.release()
        elif(count==2):
            img1 = img2 = img3
            cam = cv2.VideoCapture(0)
            message.reply('動体検知開始') # メンション
            count=0

#写真を撮影しslackへ送信
@respond_to('写真')
def picture_func(message):
    global count
    while count==1:
        message.reply('他アプリがカメラ使用中..')     # メンション
        time.sleep(20)
    count=1
    message.reply('送信中...')     # メンション
    time.sleep(2)
    cam = cv2.VideoCapture(0)
    cv2.imwrite("./slack.jpg", get_image(cam))
    slack("./slack.jpg","現在の様子","現在の様子")
    message.react('+1')
    cam.release()
    count=2

#mjpg-streamerを利用して90秒間動画をストリーミング
@respond_to('stream')
def mention_func(message):
    cmd="curl ifconfig.io"
    ip=sb.check_output(cmd.split())
    global count
    while count==1:
        message.reply('他アプリがカメラ使用中...')     # メンション
        time.sleep(20)
    count=1
    time.sleep(2)
    message.reply('90秒間ストリーミングします。')
    message.reply('自宅 http://10.211.55.56:8080/?action=stream')
    message.reply("外出先 http://"+str(ip[0:-1].decode())+":8080/?action=stream")
    stream()
    count=2
    message.reply('stream終了') # メンション

def stream():
    cmd = "sh ./mjpg.sh"
    sb.call(cmd.split())


