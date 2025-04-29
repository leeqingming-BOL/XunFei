#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
讯飞语音测评批量测试程序
用于测试多个音频文件并比较评测结果
"""

import os
import argparse
import json
import time
import pandas as pd
from test_ise import IseTest, analyze_result

def batch_test(audio_dir, test_type, text, output_dir=None):
    """
    批量测试目录下的所有音频文件
    
    Args:
        audio_dir (str): 音频文件目录
        test_type (str): 测评类型
        text (str): 测评文本
        output_dir (str): 输出目录
    
    Returns:
        dict: 测试结果
    """
    # 创建输出目录
    if not output_dir:
        output_dir = os.path.join(os.path.dirname(audio_dir), "results")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 查找所有音频文件
    audio_files = []
    for root, _, files in os.walk(audio_dir):
        for file in files:
            if file.endswith((".mp3", ".wav")):
                audio_files.append(os.path.join(root, file))
    
    if not audio_files:
        print(f"在 {audio_dir} 中未找到音频文件")
        return {}
    
    print(f"发现 {len(audio_files)} 个音频文件")
    results = {}
    
    # 批量测试每个音频文件
    for i, audio_file in enumerate(audio_files):
        print(f"\n[{i+1}/{len(audio_files)}] 测试文件: {audio_file}")
        
        try:
            # 执行测评
            tester = IseTest(audio_file, test_type, text)
            result_xml = tester.run()
            
            if result_xml:
                # 分析结果
                analyzed = analyze_result(result_xml)
                
                # 保存结果
                file_name = os.path.basename(audio_file)
                base_name = os.path.splitext(file_name)[0]
                
                # 保存解析后的结果
                summary_path = os.path.join(output_dir, f"{base_name}_summary.txt")
                with open(summary_path, "w", encoding="utf-8") as f:
                    f.write("=== 评测结果摘要 ===\n")
                    for key, value in analyzed.items():
                        if key != "原始数据":
                            f.write(f"{key}: {value}\n")
                
                # 保存原始XML
                xml_path = os.path.join(output_dir, f"{base_name}_xml.txt")
                with open(xml_path, "w", encoding="utf-8") as f:
                    f.write(result_xml)
                
                # 保存到总结果
                results[file_name] = analyzed
                
                print(f"保存结果: {summary_path}")
            else:
                print(f"未能获取 {file_name} 的评测结果")
            
            # 避免频繁请求
            time.sleep(1)
        
        except Exception as e:
            print(f"处理文件 {audio_file} 时出错: {str(e)}")
    
    # 保存所有结果到JSON文件
    json_path = os.path.join(output_dir, "all_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 生成对比报告
    generate_comparison(results, output_dir)
    
    return results

def generate_comparison(results, output_dir):
    """
    生成评测结果对比报告
    
    Args:
        results (dict): 所有评测结果
        output_dir (str): 输出目录
    """
    if not results:
        print("无结果可对比")
        return
    
    # 提取所有维度
    all_dimensions = set()
    for result in results.values():
        all_dimensions.update(result.keys())
    
    # 排除非分数字段
    excluded_fields = {"error", "原始数据", "评测状态", "异常情况", "time_len", "content", "beg_pos", "end_pos", "word_count"}
    dimensions = [d for d in all_dimensions if d not in excluded_fields]
    
    # 从各个结果中提取分数
    comparison_data = []
    for file_name, result in results.items():
        row = {"音频文件": file_name}
        for dim in dimensions:
            if dim in result:
                try:
                    row[dim] = float(result[dim])
                except (ValueError, TypeError):
                    row[dim] = result[dim]
            else:
                row[dim] = None
        comparison_data.append(row)
    
    # 转换为DataFrame
    if comparison_data:
        df = pd.DataFrame(comparison_data)
        
        # 排序
        df = df.sort_values(by="总分", ascending=False)
        
        # 保存为CSV
        csv_path = os.path.join(output_dir, "comparison.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        
        # 保存为Excel
        excel_path = os.path.join(output_dir, "comparison.xlsx")
        df.to_excel(excel_path, index=False)
        
        print(f"对比报告已保存到: {csv_path} 和 {excel_path}")
        
        # 打印简单摘要
        print("\n=== 评测结果对比 ===")
        print(df[["音频文件", "总分"]].to_string(index=False))
        
        # 分析是否能区分不同speaker
        if len(df) > 1:
            score_range = df["总分"].max() - df["总分"].min()
            if score_range > 10:
                print("\n系统能够明显区分不同的朗读者，分数差异较大")
            elif 5 < score_range <= 10:
                print("\n系统可以区分不同的朗读者，但分数差异不大")
            else:
                print("\n系统对不同朗读者的区分度较低")

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description="讯飞语音评测批量测试工具")
    parser.add_argument("--dir", type=str, required=True, help="音频文件目录")
    parser.add_argument("--type", type=str, default="en_sentence", 
                        choices=["en_word", "en_sentence", "en_chapter", "cn_word", "cn_sentence", "cn_chapter"],
                        help="测评类型")
    parser.add_argument("--text", type=str, default="nice to meet you.", help="测评文本")
    parser.add_argument("--output", type=str, help="输出目录")
    
    args = parser.parse_args()
    
    # 检查目录是否存在
    if not os.path.exists(args.dir):
        print(f"错误: 目录 {args.dir} 不存在")
        return
    
    # 执行批量测试
    batch_test(args.dir, args.type, args.text, args.output)

if __name__ == "__main__":
    main() 