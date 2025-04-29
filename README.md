激活虚拟环境:
   source venv/bin/activate

测试单个音频文件:
   python3 test_ise.py --audio audio_samples/sample1.mp3 --type en_sentence --text "nice to meet you."

批量测试多个音频文件:
   python3 batch_test.py --dir audio_samples --type en_sentence --text "nice to meet you."

录制自己的音频进行对比测试:
   python3 collect_audio.py record --output my_voice.wav --convert

# 录制新的音频样本
python3 collect_audio.py record --output speaker2.wav --convert

# 批量测试
python3 batch_test.py --dir audio_samples --type en_sentence --text "nice to meet you."



# 讯飞语音评测测试工具

本项目用于测试讯飞开放平台的语音评测能力，支持评测不同朗读者的音频，分析评测结果的维度信息，并判断系统是否能区分不同的speaker。

## 功能特点

- 支持多种评测类型：中英文单词、句子、篇章朗读
- 支持多维度分数分析：总分、准确度、流畅度、完整度等
- 支持批量测试并对比不同音频文件的评测结果
- 提供音频录制和处理工具，方便准备测试数据
- 支持分析系统对不同朗读者的区分能力

## 环境准备

1. 安装依赖库

```bash
pip install websocket-client pyaudio pydub pandas openpyxl
```

2. 准备讯飞开放平台账号和应用

- 注册讯飞开放平台账号：https://www.xfyun.cn/
- 创建应用并开通语音评测能力
- 获取应用的APPID、API Key和API Secret，并更新到`test_ise.py`文件中相应位置

## 使用说明

### 1. 单个音频测试

使用`test_ise.py`脚本测试单个音频文件：

```bash
python test_ise.py --audio ise_python3/1.mp3 --type en_sentence --text "nice to meet you."
```

参数说明：
- `--audio`: 音频文件路径
- `--type`: 评测类型，可选值：
  - `en_word`: 英文单词
  - `en_sentence`: 英文句子
  - `en_chapter`: 英文篇章
  - `cn_word`: 中文单词
  - `cn_sentence`: 中文句子
  - `cn_chapter`: 中文篇章
- `--text`: 评测文本
- `--output`: 输出文件路径（可选）

### 2. 批量测试多个音频

使用`batch_test.py`脚本批量测试目录下的所有音频文件：

```bash
python batch_test.py --dir audio_samples --type en_sentence --text "nice to meet you."
```

参数说明：
- `--dir`: 音频文件目录
- `--type`: 评测类型，同上
- `--text`: 评测文本
- `--output`: 输出目录（可选）

### 3. 录制和处理音频

使用`collect_audio.py`脚本录制和处理音频文件：

#### 录制音频

```bash
python collect_audio.py record --duration 5 --convert
```

参数说明：
- `--output`: 输出文件路径（可选）
- `--duration`: 录制时长（秒）
- `--sample-rate`: 采样率（默认16000）
- `--convert`: 是否转换为MP3格式

#### 转换音频格式

```bash
python collect_audio.py convert --input recording.wav
```

参数说明：
- `--input`: 输入文件路径
- `--output`: 输出文件路径（可选）

#### 批量处理音频

```bash
python collect_audio.py process --input audio_raw
```

参数说明：
- `--input`: 输入目录
- `--output`: 输出目录（可选）
- `--no-convert`: 不转换为MP3（可选）

## 完成需求的步骤

按照以下步骤完成讯飞开放平台语音评测能力的测试需求：

1. **准备测试音频**

   收集不同人朗读相同文本的音频文件：
   ```bash
   # 录制自己的朗读
   python collect_audio.py record --output my_reading.wav --convert
   
   # 或者准备多个WAV文件并转换为MP3
   python collect_audio.py process --input raw_audio --output audio_samples
   ```

2. **测试单个文件**

   先测试单个音频文件，查看评测结果的维度信息：
   ```bash
   python test_ise.py --audio audio_samples/speaker1.mp3 --type en_sentence --text "nice to meet you."
   ```

3. **批量测试对比**

   测试多个不同朗读者的音频文件并对比结果：
   ```bash
   python batch_test.py --dir audio_samples --type en_sentence --text "nice to meet you."
   ```

4. **分析结果**

   - 查看生成的结果文件：
     - `results/comparison.csv`: 所有音频评测结果对比
     - `results/all_results.json`: 详细JSON格式结果
     - 各个音频文件的单独结果和XML数据
   
   - 分析维度信息：总分、准确度、流畅度、完整度等各个维度的评分
   
   - 判断系统是否能区分不同speaker：对比不同朗读者的评分差异

## 项目文件说明

- `test_ise.py`: 单个音频测试脚本
- `batch_test.py`: 批量测试脚本
- `collect_audio.py`: 音频收集和处理脚本
- `ise_python3/`: 讯飞提供的原始demo代码及音频
- `README.md`: 使用说明文档

## 注意事项

1. 确保音频文件符合讯飞语音评测的要求：16kHz采样率、单声道
2. 测试文本需要和音频内容一致
3. 使用录音功能需要确保计算机有可用的麦克风设备
4. 讯飞开放平台有API调用次数限制，注意控制测试频率 