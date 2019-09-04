### 使用ライブラリ
	https://github.com/opencv/opencv/

### 写真の撮影
	piカメラを使った写真を撮影する方法
		1, 写真を保存したいディレクトリに行く
		2, raspistill -o [保存したい名前]
		   をbashで叩く 

### room_data 温度などの、カメラ画像以外のラズパイ
pip3 isntall getrpimodel
pip3 install smbus2
pip3 install boto3
