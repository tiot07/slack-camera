gtimeout 90 ../mjpg-streamer/mjpg-streamer/mjpg_streamer -i "../mjpg-streamer/mjpg-streamer/input_uvc.so -d /dev/video0 -r 1280x720 -f 30 -y -n" -o "../mjpg-streamer/mjpg-streamer/output_http.so -w ../mjpg-streamer/mjpg-streamer//www -p 8080 -c user:password"