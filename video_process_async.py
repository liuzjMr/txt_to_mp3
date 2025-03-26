import os
import sys
import shutil
import subprocess
import platform
from typing import Optional

def get_base_path():
    """获取项目基础路径"""
    return os.path.dirname(os.path.abspath(__file__))

def get_ffmpeg_path():
    """获取ffmpeg路径"""
    base_path = get_base_path()
    return os.path.join(base_path, "ffmpeg", "ffmpeg.exe")

def create_video(mp3_path: str, image_path: str, output_path: str) -> Optional[str]:
    try:
        # 创建临时输出目录
        tmp_dir = os.path.join(os.path.dirname(output_path), "tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        
        # 创建临时输出文件路径
        tmp_output = os.path.join(tmp_dir, os.path.basename(output_path))
        
        # 计算480p分辨率
        width = 854  # 16:9 比例下的宽度
        height = 480
        
        cmd = [
            get_ffmpeg_path(),
            '-loop', '1',
            '-i', image_path,
            '-i', mp3_path,
            '-c:v', 'h264',
            '-preset', 'medium',
            '-tune', 'stillimage',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest',
            '-s', f'{width}x{height}',
            '-y',
            tmp_output
        ]
        
        # 使用 CREATE_NO_WINDOW 标志来隐藏控制台窗口
        startupinfo = None
        if platform.system() == 'Windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        # 执行命令，使用 utf-8 编码
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            encoding='utf-8',
            errors='ignore'
        )
        
        # 等待处理完成
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            # 如果失败，清理临时文件
            if os.path.exists(tmp_output):
                os.remove(tmp_output)
            return f"视频合成失败: {stderr}"
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 移动文件到最终位置
        shutil.move(tmp_output, output_path)
        print(f"完成视频合成: {os.path.basename(output_path)}")
        return None
        
    except Exception as e:
        # 确保清理临时文件
        if 'tmp_output' in locals() and os.path.exists(tmp_output):
            os.remove(tmp_output)
        return f"视频合成出错: {str(e)}"
    finally:
        # 清理空的临时目录
        if 'tmp_dir' in locals() and os.path.exists(tmp_dir) and not os.listdir(tmp_dir):
            os.rmdir(tmp_dir)

def process_novel_videos(novel_name: str) -> tuple[int, Optional[str]]:
    """
    处理指定小说的所有合并音频文件生成视频
    
    Args:
        novel_name: 小说名称
        
    Returns:
        tuple[int, Optional[str]]: (处理的文件数, 错误信息如果有)
    """
    base_path = get_base_path()
    merge_dir = os.path.join(base_path, "data", "out_mp3_merge", novel_name)
    out_dir = os.path.join(base_path, "data", "out_mp4", novel_name)
    
    # 检查所有支持的图片格式
    supported_formats = ['.jpg', '.jpeg', '.png']
    image_path = None
    
    for ext in supported_formats:
        temp_path = os.path.join(base_path, "data", "images", f"{novel_name}{ext}")
        if os.path.exists(temp_path):
            image_path = temp_path
            break
    
    if not image_path:
        return 0, f"找不到小说封面图片: {novel_name}"
    
    if not os.path.exists(merge_dir):
        return 0, f"找不到合并音频目录: {novel_name}"
    
    try:
        processed_count = 0
        total_files = len([f for f in os.listdir(merge_dir) if f.endswith('.mp3')])
        
        for mp3_file in os.listdir(merge_dir):
            if not mp3_file.endswith('.mp3'):
                continue
                
            # 使用相同的文件名，但改为.mp4后缀
            mp4_filename = mp3_file[:-4] + '.mp4'
            mp3_path = os.path.join(merge_dir, mp3_file)
            mp4_path = os.path.join(out_dir, mp4_filename)
            
            # 检查是否已经处理过
            if os.path.exists(mp4_path):
                processed_count += 1
                print(f"跳过已处理文件: {mp4_filename}")
                continue
            
            print(f"正在处理文件 [{processed_count + 1}/{total_files}]: {mp4_filename}")
            error = create_video(mp3_path, image_path, mp4_path)
            
            if error:
                return processed_count, error
            
            processed_count += 1
            
        return processed_count, None
        
    except Exception as e:
        return processed_count, f"处理视频时出错: {str(e)}"

def process_all_novels() -> tuple[int, Optional[str]]:
    """处理所有小说的视频生成"""
    base_path = get_base_path()
    merge_dir = os.path.join(base_path, "data", "out_mp3_merge")
    
    if not os.path.exists(merge_dir):
        return 0, "找不到合并音频目录"
    
    try:
        total_processed = 0
        novel_dirs = [d for d in os.listdir(merge_dir) if os.path.isdir(os.path.join(merge_dir, d))]
        
        for novel_name in novel_dirs:
            print(f"\n开始处理小说: {novel_name}")
            count, error = process_novel_videos(novel_name)
            
            if error:
                return total_processed, error
                
            total_processed += count
            print(f"小说 {novel_name} 处理完成，生成 {count} 个视频")
            
        return total_processed, None
        
    except Exception as e:
        return total_processed, f"处理所有小说时出错: {str(e)}"

if __name__ == "__main__":
    try:
        # 检查是否有命令行参数
        if len(sys.argv) > 1:
            # 如果有参数，处理指定的小说
            novel_name = sys.argv[1]
            count, error = process_novel_videos(novel_name)
            if error:
                print(f"处理失败: {error}")
            else:
                print(f"处理完成，共生成 {count} 个视频文件")
        else:
            # 如果没有参数，处理所有小说
            count, error = process_all_novels()
            if error:
                print(f"处理失败: {error}")
            else:
                print(f"所有小说处理完成，共生成 {count} 个视频文件")
    except Exception as e:
        print(f"处理视频时出错: {str(e)}")
        sys.exit(1)