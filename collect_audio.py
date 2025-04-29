#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频收集与处理脚本
用于录制和处理音频文件，为语音评测测试准备数据
"""

import os
import argparse
import pyaudio
import wave
import time
import pydub
from pydub import AudioSegment
import threading
import tempfile

def record_audio(output_file, duration=5, sample_rate=16000, channels=1, format_type=pyaudio.paInt16):
    """
    录制音频
    
    Args:
        output_file (str): 输出文件路径
        duration (int): 录制时长(秒)
        sample_rate (int): 采样率
        channels (int): 声道数
        format_type: 音频格式类型
    """
    chunk = 1024  # 每个缓冲区的帧数
    
    # 初始化PyAudio
    p = pyaudio.PyAudio()
    
    # 打开音频流
    stream = p.open(
        format=format_type,
        channels=channels,
        rate=sample_rate,
        input=True,
        frames_per_buffer=chunk
    )
    
    print(f"开始录音，持续 {duration} 秒...")
    
    # 倒计时
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    print("录制中...")
    
    # 显示进度的线程
    stop_flag = threading.Event()
    
    def show_progress():
        start_time = time.time()
        while not stop_flag.is_set():
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break
            percent = int((elapsed / duration) * 100)
            print(f"\r进度: {percent}% [{int(elapsed)}/{duration}秒]", end="")
            time.sleep(0.1)
    
    progress_thread = threading.Thread(target=show_progress)
    progress_thread.start()
    
    # 录制音频
    frames = []
    for i in range(0, int(sample_rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)
    
    # 停止进度显示
    stop_flag.set()
    progress_thread.join()
    
    print("\n录音完成!")
    
    # 停止并关闭流
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # 保存到WAV文件
    wf = wave.open(output_file, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format_type))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    print(f"录音已保存到: {output_file}")
    return output_file

def convert_to_mp3(wav_file, output_file=None, bitrate="40k"):
    """
    将WAV文件转换为MP3
    
    Args:
        wav_file (str): WAV文件路径
        output_file (str): 输出文件路径
        bitrate (str): 比特率
        
    Returns:
        str: MP3文件路径
    """
    if not output_file:
        output_file = os.path.splitext(wav_file)[0] + ".mp3"
    
    # 加载WAV文件
    audio = AudioSegment.from_wav(wav_file)
    
    # 调整采样率为16kHz (如果需要)
    if audio.frame_rate != 16000:
        audio = audio.set_frame_rate(16000)
    
    # 转换为单声道 (如果需要)
    if audio.channels > 1:
        audio = audio.set_channels(1)
    
    # 导出为MP3
    audio.export(output_file, format="mp3", bitrate=bitrate)
    
    print(f"已转换为MP3: {output_file}")
    return output_file

def process_directory(input_dir, output_dir=None, convert=True):
    """
    处理目录中的所有WAV文件，转换为MP3
    
    Args:
        input_dir (str): 输入目录
        output_dir (str): 输出目录
        convert (bool): 是否转换为MP3
    """
    if not os.path.exists(input_dir):
        print(f"错误: 目录 {input_dir} 不存在")
        return
    
    if not output_dir:
        output_dir = os.path.join(os.path.dirname(input_dir), "processed")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 查找所有WAV文件
    wav_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".wav"):
                wav_files.append(os.path.join(root, file))
    
    if not wav_files:
        print(f"在 {input_dir} 中未找到WAV文件")
        return
    
    print(f"找到 {len(wav_files)} 个WAV文件")
    
    # 处理每个文件
    for i, wav_file in enumerate(wav_files):
        print(f"\n[{i+1}/{len(wav_files)}] 处理: {wav_file}")
        file_name = os.path.basename(wav_file)
        base_name = os.path.splitext(file_name)[0]
        
        if convert:
            # 转换为MP3
            output_file = os.path.join(output_dir, base_name + ".mp3")
            convert_to_mp3(wav_file, output_file)
        else:
            # 仅复制
            import shutil
            output_file = os.path.join(output_dir, file_name)
            shutil.copy2(wav_file, output_file)
            print(f"已复制: {output_file}")

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description="音频收集与处理工具")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 录制命令
    record_parser = subparsers.add_parser("record", help="录制音频")
    record_parser.add_argument("--output", type=str, help="输出文件路径")
    record_parser.add_argument("--duration", type=int, default=5, help="录制时长(秒)")
    record_parser.add_argument("--sample-rate", type=int, default=16000, help="采样率")
    record_parser.add_argument("--convert", action="store_true", help="转换为MP3")
    
    # 转换命令
    convert_parser = subparsers.add_parser("convert", help="转换音频格式")
    convert_parser.add_argument("--input", type=str, required=True, help="输入文件路径")
    convert_parser.add_argument("--output", type=str, help="输出文件路径")
    
    # 处理目录命令
    process_parser = subparsers.add_parser("process", help="处理目录中的所有WAV文件")
    process_parser.add_argument("--input", type=str, required=True, help="输入目录")
    process_parser.add_argument("--output", type=str, help="输出目录")
    process_parser.add_argument("--no-convert", action="store_true", help="不转换为MP3")
    
    args = parser.parse_args()
    
    if args.command == "record":
        # 设置默认输出文件
        if not args.output:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            args.output = f"recording_{timestamp}.wav"
        
        # 录制音频
        wav_file = record_audio(args.output, args.duration, args.sample_rate)
        
        # 转换为MP3
        if args.convert:
            convert_to_mp3(wav_file)
    
    elif args.command == "convert":
        if not os.path.exists(args.input):
            print(f"错误: 文件 {args.input} 不存在")
            return
        
        convert_to_mp3(args.input, args.output)
    
    elif args.command == "process":
        process_directory(args.input, args.output, not args.no_convert)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 