import os
import re
import asyncio
import edge_tts
import shutil  # 添加 shutil 模块导入

def get_base_path():
    """获取项目基础路径"""
    return os.path.dirname(os.path.abspath(__file__))

def get_converted_chapters(mp3_dir):
    """获取已转换的章节列表"""
    if not os.path.exists(mp3_dir):
        return set()
    
    converted = set()
    for file in os.listdir(mp3_dir):
        if file.endswith('.mp3'):
            converted.add(file[:-4])
    return converted

def count_converted_chapters():
    """统计已转换的章节总数"""
    base_path = get_base_path()
    mp3_dir = os.path.join(base_path, "data", "out_mp3")
    count = 0
    
    if os.path.exists(mp3_dir):
        for novel_dir in os.listdir(mp3_dir):
            novel_path = os.path.join(mp3_dir, novel_dir)
            if os.path.isdir(novel_path):
                count += len([f for f in os.listdir(novel_path) if f.endswith('.mp3')])
    
    return count

def process_tts(voice="zh-CN-YunxiNeural", rate="+0%", total_chapters=0):
    """处理语音转换的主函数"""
    while True:
        converted_count = 0
        base_path = get_base_path()
        text_dir = os.path.join(base_path, "data", "out_text")
        
        # 处理所有小说目录
        for novel_dir in os.listdir(text_dir):
            novel_path = os.path.join(text_dir, novel_dir)
            if os.path.isdir(novel_path):
                # 创建对应的MP3输出目录
                mp3_dir = os.path.join(base_path, "data", "out_mp3", novel_dir)
                os.makedirs(mp3_dir, exist_ok=True)
                
                # 获取已转换的章节列表
                converted_chapters = get_converted_chapters(mp3_dir)
                
                # 处理每个章节前创建临时目录
                tmp_dir = os.path.join(mp3_dir, "tmp")
                os.makedirs(tmp_dir, exist_ok=True)
                
                try:
                    # 处理每个章节
                    for chapter_file in os.listdir(novel_path):
                        if chapter_file.endswith('.txt'):
                            # 检查是否已转换
                            chapter_name = chapter_file[:-4]
                            if chapter_name in converted_chapters:
                                print(f"跳过已转换章节: {chapter_file}")
                                continue
                            
                            # 读取文本内容
                            text_path = os.path.join(novel_path, chapter_file)
                            with open(text_path, 'r', encoding='utf-8') as f:
                                text = f.read()
                            
                            # 设置临时输出路径和最终输出路径
                            mp3_filename = chapter_file.replace('.txt', '.mp3')
                            mp3_filename = re.sub(r'[<>:"/\\|?*]', '_', mp3_filename)
                            tmp_path = os.path.join(tmp_dir, mp3_filename)
                            final_path = os.path.join(mp3_dir, mp3_filename)
                            
                            try:
                                # 转换语音到临时文件
                                print(f"正在转换: {mp3_filename}")
                                asyncio.run(text_to_speech(text, tmp_path, voice, rate))
                                
                                # 转换成功后移动到最终目录
                                if os.path.exists(tmp_path):
                                    shutil.move(tmp_path, final_path)
                                    converted_count += 1
                                    print(f"已完成: {mp3_filename}")
                            except Exception as e:
                                print(f"转换失败: {mp3_filename}, 错误: {str(e)}")
                                # 清理可能存在的临时文件
                                if os.path.exists(tmp_path):
                                    os.remove(tmp_path)
                finally:
                    # 在处理完所有章节后清理临时目录
                    try:
                        if os.path.exists(tmp_dir):
                            shutil.rmtree(tmp_dir)
                    except Exception as e:
                        print(f"清理临时目录失败: {str(e)}")
        
        # 所有章节处理完成后的检查逻辑
        total_converted = count_converted_chapters()
        print(f"本轮转换完成，已转换 {total_converted}/{total_chapters} 章节")
        
        if total_chapters > 0 and total_converted < total_chapters:
            print("检测到有未转换的章节，开始新一轮转换...")
            continue
        else:
            print(f"所有章节均已转换完成，共 {total_converted} 章节")
            break
    
    return total_converted

async def text_to_speech(text, output_path, voice, rate):
    """将文本转换为语音"""
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)

def get_chinese_voices():
    """获取中文语音列表"""
    voices = [
        "zh-CN-XiaoxiaoNeural",
        "zh-CN-XiaoyiNeural",
        "zh-CN-YunjianNeural",
        "zh-CN-YunxiNeural",
        "zh-CN-YunxiaNeural",
        "zh-CN-YunyangNeural"
    ]
    return voices

if __name__ == "__main__":
    import sys
    
    # 获取命令行参数
    voice = sys.argv[1]
    rate = sys.argv[2]
    total_chapters = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    
    try:
        # 执行转换直到所有章节都完成
        count = process_tts(voice, rate, total_chapters)
        print(f"转换完成，共转换 {count} 个章节")
    except Exception as e:
        print(f"转换失败: {str(e)}")