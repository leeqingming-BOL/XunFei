#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
讯飞语音测评API测试程序
用于测试语音评测功能并分析结果维度
"""

import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import os
import xml.etree.ElementTree as ET
import argparse

# 讯飞开放平台配置
host_url = "ws://ise-api.xfyun.cn/v2/open-ise"
appid = "be806498"  # 控制台获取
api_secret = "MTVjOTBkMTEyNmYyZTdhODMxNDI2YTYy"
api_key = "90c93db93bf80f3ca253d0ddf90f86c2"

# 测评类型配置
CATEGORY_TYPES = {
    "cn_word": {"category": "read_word", "ent": "cn_vip", "group": "pupil"},
    "cn_sentence": {"category": "read_sentence", "ent": "cn_vip", "group": "pupil"},
    "cn_chapter": {"category": "read_chapter", "ent": "cn_vip", "group": "pupil"},
    "en_word": {"category": "read_word", "ent": "en_vip", "group": "pupil"},
    "en_sentence": {"category": "read_sentence", "ent": "en_vip", "group": "pupil"},
    "en_chapter": {"category": "read_chapter", "ent": "en_vip", "group": "pupil"},
}

def generate_url(api_secret, api_key):
    """
    生成WebSocket连接URL
    """
    now_time = datetime.now()
    now_date = format_date_time(mktime(now_time.timetuple()))
    
    # 构建签名原始字符串
    origin_base = "host: " + "ise-api.xfyun.cn" + "\n"
    origin_base += "date: " + now_date + "\n"
    origin_base += "GET " + "/v2/open-ise " + "HTTP/1.1"
    
    # 使用hmac-sha256算法进行签名
    signature_sha = hmac.new(api_secret.encode('utf-8'), origin_base.encode('utf-8'),
                            digestmod=hashlib.sha256).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
    
    # 构建授权字符串
    authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
        api_key, "hmac-sha256", "host date request-line", signature_sha)
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    
    # 构建请求URL
    dict_data = {
        "authorization": authorization,
        "date": now_date,
        "host": "ise-api.xfyun.cn"
    }
    ws_url = host_url + '?' + urlencode(dict_data)
    return ws_url

class IseTest(object):
    def __init__(self, audio_file, test_type="en_sentence", text=None):
        self.audio_file = audio_file
        self.test_type = test_type
        self.text = text if text else "nice to meet you."
        self.result = None
        self.ws_url = generate_url(api_secret, api_key)
        
        # 获取评测配置
        self.category = CATEGORY_TYPES[test_type]["category"]
        self.ent = CATEGORY_TYPES[test_type]["ent"]
        self.group = CATEGORY_TYPES[test_type]["group"]
    
    def on_message(self, ws, message):
        """
        接收消息回调
        """
        data = json.loads(message)
        code = data["code"]
        sid = data["sid"]
        status = data["data"]["status"]
        
        print(f"接收消息: sid={sid}, status={status}, code={code}")
        
        if status == 2:
            xml_data = base64.b64decode(data["data"]["data"])
            self.result = xml_data.decode("utf-8")
            print("评测结果已接收")
            ws.close()

    def on_error(self, ws, error):
        """
        错误回调
        """
        print(f"连接错误: {error}")

    def on_close(self, ws, close_status_code, close_reason):
        """
        连接关闭回调
        """
        print(f"连接关闭: code={close_status_code}, reason={close_reason}")

    def on_open(self, ws):
        """
        连接建立回调
        """
        print(f"连接已建立")
        
        # 构建第一帧数据，包含评测参数
        send_dict = {
            "common": {
                "app_id": appid
            },
            "business": {
                "category": self.category,
                "rstcd": "utf8",
                "sub": "ise",
                "group": self.group,
                "ent": self.ent,
                "tte": "utf-8",
                "cmd": "ssb",
                "auf": "audio/L16;rate=16000",
                "aue": "lame",
                "text": '\uFEFF' + f"[content]\n{self.text}"
            },
            "data": {
                "status": 0,
                "data": ""
            }
        }
        
        # 如果是进阶测评，添加多维度分析参数
        if "extra_ability" not in send_dict["business"]:
            send_dict["business"]["extra_ability"] = "multi_dimension_score"
        
        # 发送第一帧数据(参数帧)
        ws.send(json.dumps(send_dict))
        
        # 读取音频文件并发送
        with open(self.audio_file, "rb") as f:
            audio_data = f.read()
            
        # 计算每一帧大小和数量
        frame_size = 1280
        frames = [audio_data[i:i+frame_size] for i in range(0, len(audio_data), frame_size)]
        
        # 发送音频数据
        for i, frame in enumerate(frames):
            # 第一帧
            if i == 0:
                send_dict = {
                    "business": {
                        "cmd": "auw",
                        "aus": 1,
                        "aue": "lame"
                    },
                    "data": {
                        "status": 1,
                        "data": str(base64.b64encode(frame).decode()),
                        "data_type": 1,
                        "encoding": "raw"
                    }
                }
            # 最后一帧
            elif i == len(frames) - 1:
                send_dict = {
                    "business": {
                        "cmd": "auw", 
                        "aus": 4,
                        "aue": "lame"
                    },
                    "data": {
                        "status": 2, 
                        "data": str(base64.b64encode(frame).decode())
                    }
                }
                print("发送最后一帧数据")
            # 中间帧
            else:
                send_dict = {
                    "business": {
                        "cmd": "auw",
                        "aus": 2,
                        "aue": "lame"
                    },
                    "data": {
                        "status": 1,
                        "data": str(base64.b64encode(frame).decode()),
                        "data_type": 1,
                        "encoding": "raw"
                    }
                }
            
            # 发送音频帧
            ws.send(json.dumps(send_dict))
            time.sleep(0.04)  # 控制发送速率

    def run(self):
        """
        启动测评流程
        """
        print(f"开始测评: {self.audio_file}")
        print(f"测评类型: {self.test_type}")
        print(f"测评文本: {self.text}")
        
        start_time = datetime.now()
        websocket.enableTrace(False)
        
        # 创建WebSocket连接
        ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        
        # 运行WebSocket连接
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        end_time = datetime.now()
        print(f"评测耗时: {end_time - start_time}")
        
        return self.result

def analyze_result(xml_str):
    """
    分析XML格式的评测结果
    """
    if not xml_str:
        return {"error": "未获取到有效结果"}
    
    try:
        # 解析XML
        root = ET.fromstring(xml_str)
        
        # 获取基本信息
        result = {
            "总分": root.get("total_score"),
        }
        
        # 提取所有属性
        for child in root:
            if child.tag == "read_sentence" or child.tag == "read_chapter" or child.tag == "read_word":
                for attr, value in child.attrib.items():
                    result[f"{attr}"] = value
        
        # 添加各个维度分数
        dimensions = ["fluency_score", "integrity_score", "phone_score", "tone_score", "accuracy_score", "standard_score"]
        for dim in dimensions:
            if dim in result:
                dim_name = {
                    "fluency_score": "流畅度",
                    "integrity_score": "完整度",
                    "phone_score": "声韵分",
                    "tone_score": "调型分",
                    "accuracy_score": "准确度",
                    "standard_score": "标准度"
                }.get(dim, dim)
                result[dim_name] = result.pop(dim)
        
        # 检查是否拒识
        if "is_rejected" in result:
            if result["is_rejected"] == "true":
                result["评测状态"] = "被拒绝 (可能为乱读或者与文本不符)"
            else:
                result["评测状态"] = "正常"
            result.pop("is_rejected")
        
        # 检查是否有异常信息
        if "except_info" in result:
            except_info = result.pop("except_info")
            except_map = {
                "28673": "无语音或音量过小",
                "28676": "乱说",
                "28680": "信噪比低",
                "28690": "截幅",
                "28689": "无有效音频"
            }
            result["异常情况"] = except_map.get(except_info, f"未知异常({except_info})")
        
        return result
    
    except Exception as e:
        return {"error": f"解析结果时出错: {str(e)}", "原始数据": xml_str}

def save_result(result, output_path):
    """
    保存测评结果到文件
    """
    with open(output_path, "w", encoding="utf-8") as f:
        if isinstance(result, dict):
            f.write("=== 评测结果摘要 ===\n")
            for key, value in result.items():
                f.write(f"{key}: {value}\n")
            
            if "原始数据" in result:
                f.write("\n=== 原始XML数据 ===\n")
                f.write(result["原始数据"])
        else:
            f.write(result)
    
    print(f"结果已保存到: {output_path}")

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description="讯飞语音评测测试工具")
    parser.add_argument("--audio", type=str, required=True, help="音频文件路径")
    parser.add_argument("--type", type=str, default="en_sentence", 
                        choices=CATEGORY_TYPES.keys(),
                        help="测评类型")
    parser.add_argument("--text", type=str, help="测评文本")
    parser.add_argument("--output", type=str, help="输出文件路径")
    
    args = parser.parse_args()
    
    # 检查音频文件是否存在
    if not os.path.exists(args.audio):
        print(f"错误: 音频文件 {args.audio} 不存在")
        return
    
    # 设置默认文本
    if not args.text:
        default_texts = {
            "en_word": "hello",
            "en_sentence": "nice to meet you.",
            "en_chapter": "This is a test for English chapter reading.",
            "cn_word": "你好",
            "cn_sentence": "很高兴认识你。",
            "cn_chapter": "这是中文朗读测试。"
        }
        args.text = default_texts.get(args.type, "nice to meet you.")
    
    # 设置默认输出路径
    if not args.output:
        audio_name = os.path.basename(args.audio)
        args.output = f"result_{audio_name.split('.')[0]}_{args.type}.txt"
    
    # 执行测评
    tester = IseTest(args.audio, args.type, args.text)
    result = tester.run()
    
    if result:
        # 分析结果
        analyzed = analyze_result(result)
        
        # 打印结果摘要
        print("\n=== 评测结果摘要 ===")
        for key, value in analyzed.items():
            if key != "原始数据":
                print(f"{key}: {value}")
        
        # 保存结果
        save_result(analyzed, args.output)
        
        # 同时保存原始XML
        xml_output = f"{args.output.split('.')[0]}_xml.txt"
        with open(xml_output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"原始XML结果已保存到: {xml_output}")
    else:
        print("未获取到评测结果")

if __name__ == "__main__":
    main() 