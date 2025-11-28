#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
古籍刻本背景图生成工具
Python版本 by msyloveldx, 2025/08
原作者: shanleiguang, 2024.1.5
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math
from collections import defaultdict

class CanvasGenerator:
    """背景图生成器"""
    
    def __init__(self, cid: str):
        self.cid = cid
        self.config = defaultdict(str)
        
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        config_path = Path(f"{self.cid}.cfg")
        if not config_path.exists():
            raise FileNotFoundError(f"错误: 未找到配置文件 {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 处理行内注释
                if '#' in line and '=#' not in line:
                    line = line.split('#')[0].strip()
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 尝试转换数值
                    if value.isdigit():
                        self.config[key] = int(value)
                    elif value.replace('.', '').isdigit():
                        self.config[key] = float(value)
                    else:
                        self.config[key] = value
    @staticmethod
    def get_2points_ellipse(cd, x1, y1, x2, y2, multiplier=1):
        # 花鱼尾的弧线参数：给定两点A、B及距离两点中点距离的C，返回以C点为圆心，经过A、B两点弧线的Draw ellipse参数
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2  # 两点直线中点
        d21 = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)  # 两点直线距离
        sin21 = abs((x2 - x1) / d21)  # 两点及水平线组成的直角三角形锐角的正弦
        cos21 = abs((y2 - y1) / d21)  # 余弦
        ncx = cx - cd * cos21  # 新圆心坐标
        ncy = cy - cd * sin21  # 新圆心坐标
        cr = math.sqrt((ncx - x1) ** 2 + (ncy - y1) ** 2)  # 新圆半径
        dgrees1 = math.degrees(math.atan2(y1 - ncy, x1 - ncx))  # 反切得到弧度，弧度转为角度
        dgrees2 = math.degrees(math.atan2(y2 - ncy, x2 - ncx))
        return [(ncx - cr) * multiplier, (ncy - cr) * multiplier, (ncx + cr) * multiplier, (ncy + cr) * multiplier],dgrees1,dgrees2

    def create_canvas(self):
        """创建背景图"""
        # 获取配置参数
        ifmr, mrn, mrlw, mrcc = self.config['if_multirows'], \
            self.config['multirows_num'], \
            self.config['multirows_linewidth'], \
            self.config['multirows_colcolor'] #多栏参数
        bg = self.config['canvas_background_image'] #背景图
        cw = int(self.config.get('canvas_width', 2480))
        ch = int(self.config.get('canvas_height', 1860))
        cc = self.config.get('canvas_color', 'white')
        
        mt = int(self.config.get('margins_top', 200))
        mb = int(self.config.get('margins_bottom', 50))
        ml = int(self.config.get('margins_left', 50))
        mr = int(self.config.get('margins_right', 50))
        
        cln = int(self.config.get('leaf_col', 24))
        lcw = int(self.config.get('leaf_center_width', 120))
        
        # 鱼尾参数
        fty = int(self.config.get('fish_top_y', 500))
        ftc = self.config.get('fish_top_color', 'black')
        ftrh = int(self.config.get('fish_top_rectheight', 50))
        ftth = int(self.config.get('fish_top_triaheight', 30))
        ftlw = int(self.config.get('fish_top_linewidth', 15))
        
        fbd = int(self.config.get('fish_btm_direction', 1))
        fby = int(self.config.get('fish_btm_y', 1500))
        fbc = self.config.get('fish_btm_color', 'black')
        fbrh = int(self.config.get('fish_btm_rectheight', 50))
        fbth = int(self.config.get('fish_btm_triaheight', 30))
        fblw = int(self.config.get('fish_btm_linewidth', 15))
        
        flw = int(self.config.get('fish_line_width', 1))
        flm = int(self.config.get('fish_line_margin', 5))
        flc = self.config.get('fish_line_color', 'black')
        iff, ffi = self.config['if_fishflower'], self.config['fish_flower_image'] #花鱼尾，花鱼尾装饰图
        
        # 线条参数
        ilw = int(self.config.get('inline_width', 1))
        ilc = self.config.get('inline_color', 'black')
        olw = int(self.config.get('outline_width', 10))
        olc = self.config.get('outline_color', 'black')
        moh = int(self.config.get('outline_hmargin', 5))
        mov = int(self.config.get('outline_vmargin', 5))
        
        # 文字参数
        lgi = self.config['logo_image'] #logo图
        lgt = self.config.get('logo_text', '')
        lgy = int(self.config.get('logo_y', 1680))
        lgc = self.config.get('logo_color', 'white')
        lgf = "../fonts/" + self.config.get('logo_font', 'qiji-combo.ttf')
        lgs = int(self.config.get('logo_font_size', 40))
        
        clw = (cw - ml - mr - lcw) / cln
        
        print('-' * 60)
        print(f"创建 '{self.cid}' 背景图 ... ")
        print('-' * 60)
        print(f"\t背景尺寸：{cw} x {ch}")
        print(f"\t背景颜色：{cc}\t背景图片：{bg if bg else '无'}")
        print(f"\t整叶列数：{cln}\t版心宽度：{lcw}")
        print(f"\t四边边距：上{mt} 下{mb} 左{ml} 右{mr}")
        print(f"\t外框线宽：{olw}\t外框颜色：{olc}")
        print(f"\t内框线宽：{ilw}\t内框颜色：{ilc}")
        print(f"\t内外框距：横{moh} 纵{mov}")
        print(f"\t多栏模式：{str(mrn) + '栏' if ifmr else '否'}\t分栏线宽：{mrlw if mrlw else ''}\t栏列线色：{mrcc if mrcc else ''}")
        print(f"\t是否花尾：{'是' if iff else '否'}\t鱼尾装饰：{ffi if ffi else '无'} *鱼尾装饰图应为正方形且内容居中")
        print(f"\t鱼尾对顺：{'顺鱼尾' if fbd == 0 else '对鱼尾'}")
        print(f"\t鱼尾高度：上{fty} 下{fby} *以左上角为原点")
        print(f"\t上尾身长：{ftrh}\t上尾尾长：{ftth}")
        print(f"\t下尾身长：{fbrh}\t下尾尾长：{fbth}")
        print(f"\t个性印章：{lgi if lgi else '无'}\t个性签名：{lgt if lgt else '无'}")
        print('-' * 60)
        
        # 创建图像
        if bg and Path(bg).exists():
            cimg = Image.open(bg).convert('RGB')
            cimg = cimg.resize((cw, ch), Image.LANCZOS)
        else:
            cimg = Image.new('RGB', (cw, ch), color=cc)
        draw = ImageDraw.Draw(cimg)
        
        limg = Image.new("RGBA", (cw, ch))
    
        delta = 5 #标准间距
        gr = 0.618 #黄金分割率
        # 粗外框
        draw.rectangle([ml - olw - moh - delta, mt - olw - mov - delta, 
                       cw - mr + olw + moh + delta, ch - mb + olw + mov + delta],
                      outline=olc, width=olw)

        # 细内框
        draw.rectangle([ml - delta, mt - delta, cw - mr + delta, ch - mb + delta], 
                      outline=ilc, width=ilw)
        
        # 列细线
        for cid in range(1, cln + 1):
            tilc = mrcc if ifmr and mrn > 1 else ilc  # 多栏模式时，更新栏内列细线颜色
            if cid == cln // 2 or cid == cln // 2 + 1:
                tilc = ilc  # 版心两侧列细线
            wd = (lcw - clw) if cid > cln // 2 else 0  # 对于越过版心列的横坐标调整
            draw.line([ml + wd + clw * cid, mt, ml + wd + clw * cid, ch - mb], fill=ilc, width=ilw)

        # 多栏模式时打印分栏横线
        if ifmr and mrn > 1:
            mrh = (ch - mt - mb) / mrn
            for rid in range(1, mrn):
                draw.line([ml, mt + rid * mrh, cw / 2 - lcw / 2, mt + rid * mrh], fill=ilc, width=mrlw)
                draw.line([cw - mr, mt + rid * mrh, cw / 2 + lcw / 2, mt + rid * mrh], fill=ilc, width=mrlw)

        # 绘制鱼尾
        self._draw_fish_top(draw, cw, fty, ftrh, ftth, flc, flw, ftc, lcw, flm, iff)
        
        if fbd == 0:
            self._draw_fish_btm_down(draw, cw, fby, fbrh, fbth, flc, flw, fbc, lcw, flm, iff)
        elif fbd == 1:
            self._draw_fish_btm_up(draw, cw, fby, fbrh, fbth, flc, flw, fbc, lcw, flm, mt, mb, mov, iff)

        # 花鱼尾装饰图，要求：正方形，透明底色，主体图案为白色
        if ffi and os.path.isfile(ffi):
            # 三叶草图层
            # 将装饰图缩小为鱼尾尾部高度的黄金分割比例尺寸，距版心左、右侧线距离为delta并与鱼身高度对齐
            fimg1 = Image.open(ffi).convert("RGBA")
            fw, fh = int(ftrh * gr), int(ftrh * gr)
            multiplier = 5
            fimg1 = fimg1.resize((fw * multiplier, fh * multiplier), Image.LANCZOS)
            fimg1 = fimg1.rotate(30, expand=True, resample=Image.BICUBIC)
            fimg1 = fimg1.resize((int(fw * 1.4), int(fh * 1.4)), Image.LANCZOS)
            fimg2 = fimg1.transpose(Image.FLIP_LEFT_RIGHT)
            fimg3 = fimg1.transpose(Image.FLIP_TOP_BOTTOM)
            fimg4 = fimg2.transpose(Image.FLIP_TOP_BOTTOM)
            fw, fh = fimg1.size
            limg.paste(fimg1, (int(cw/2-lcw/2+delta), int(fty+ftrh-fh)), fimg1)
            fw, fh = fimg2.size
            limg.paste(fimg2, (int(cw/2+lcw/2-fw-delta), int(fty+ftrh-fh)), fimg2)
            if fbrh > 0 and fbth > 0:
                if fbd == 0:  # 顺鱼尾
                    fw, fh = fimg3.size
                    limg.paste(fimg3, (int(cw/2-lcw/2+delta), int(fby+fbrh-fh)), fimg3)
                    fw, fh = fimg4.size
                    limg.paste(fimg4, (int(cw/2+lcw/2-fw-delta), int(fby+fbrh-fh)), fimg4)
                if fbd == 1:  # 对鱼尾
                    fw, fh = fimg3.size
                    limg.paste(fimg3, (int(cw/2-lcw/2+delta), int(fby-fbrh)), fimg3)
                    fw, fh = fimg4.size
                    limg.paste(fimg4, (int(cw/2+lcw/2-fw-delta), int(fby-fbrh)), fimg4)

        # 花鱼尾，弧形花鱼尾
        if iff:
            # 弧形花鱼尾图层
            multiplier = 5  # 放大倍数，提升绘图精度
            ew = int(lcw / 2 * multiplier)
            eh = int((ftth + 10) * multiplier)
            eimg = Image.new("RGBA", (ew, eh), (0, 0, 0, 0))
            edraw = ImageDraw.Draw(eimg)
            dd = math.sqrt((lcw/2)**2 + ftth**2)
            dsin = ftth * 1.0/ dd
            dcos = (lcw/2.0) / dd
            ddr = 0.4
            # 第一段填充弧形
            points=self.get_2points_ellipse(14, lcw/2-2*dcos, 2*dsin, lcw/2-(dd*ddr-2)*dcos, (dd*ddr-2)*dsin, multiplier)
            edraw.ellipse(points[0], fill=ftc)
            # 第一段弧线
            points = self.get_2points_ellipse(10, lcw/2, 0, lcw/2-dd*ddr*dcos, dd*ddr*dsin, multiplier)
            edraw.arc(points[0], points[1], points[2], fill=ftc, width=multiplier)
            # 第二段带填充弧形
            points = self.get_2points_ellipse(14, lcw/2-(dd*ddr+2)*dcos, (dd*ddr+2)*dsin, lcw/2-(dd-2)*dcos, (dd-2)*dsin, multiplier)
            edraw.ellipse(points[0], fill=ftc)
            # 第二段弧线
            points = self.get_2points_ellipse(10, lcw/2-dd*ddr*dcos, dd*ddr*dsin, 0, ftth, multiplier)
            edraw.arc(points[0], points[1], points[2], fill=ftc, width=multiplier)
            eimg = eimg.resize((ew // multiplier, eh // multiplier), Image.LANCZOS)
            limg.paste(eimg, (int(cw/2-lcw/2), int(fty+ftrh)), eimg)  # 左上
            eimg_flop = eimg.transpose(Image.FLIP_LEFT_RIGHT)
            limg.paste(eimg_flop, (int(cw/2), int(fty+ftrh)), eimg_flop)  # 右上
            if fbrh > 0 and fbth > 0:
                if fbd == 0:  # 顺鱼尾时
                    limg.paste(eimg_flop, (int(cw/2), int(fby+fbrh)), eimg_flop)  # 右下
                    eimg_flop2 = eimg_flop.transpose(Image.FLIP_LEFT_RIGHT)
                    limg.paste(eimg_flop2, (int(cw/2-lcw/2), int(fby+fbrh)), eimg_flop2)  # 左下
                if fbd == 1:  # 对鱼尾时
                    eimg_flip = eimg_flop.transpose(Image.FLIP_TOP_BOTTOM)
                    limg.paste(eimg_flip, (int(cw/2), int(fby-fbrh-fbth-9)), eimg_flip)  # 右下
                    eimg_flip_flop = eimg_flip.transpose(Image.FLIP_LEFT_RIGHT)
                    limg.paste(eimg_flip_flop, (int(cw/2-lcw/2), int(fby-fbrh-fbth-9)), eimg_flip_flop)  # 左下

        # 绘制鱼尾连接线
        if ftlw:
            draw.line([cw//2, mt - mov - delta, cw//2, fty - flm], fill=flc, width=ftlw)
        if fblw:
            draw.line([cw//2, fby + flm, cw//2, ch - mb + mov + delta], fill=flc, width=fblw)
        
        # 合并图层
        cimg.paste(limg, (0, 0), limg)

        if lgi and Path(lgi).exists():
            # 绘制logo图
            logo = Image.open(lgi).convert('RGBA')
            lw, lh = logo.size
            logo = logo.resize((lw // 3, lh // 3), Image.LANCZOS)
            cimg.paste(logo, (cw//2 + lcw // 4 - lw //3 // 2, ch - mb - lh // 3), logo)
        elif lgt:
            # 绘制文字
            try:
                font_path = Path(lgf)
                if not font_path.exists():
                    # 尝试在当前目录查找字体文件
                    font_path = Path(f"./{lgf}")
                
                if font_path.exists():
                    font = ImageFont.truetype(str(font_path), lgs)
                else:
                    # 使用默认字体
                    font = ImageFont.load_default()
                    print(f"警告：未找到字体文件 {lgf}，使用默认字体")
                
                for i, char in enumerate(lgt):
                    print(f"\t{char} -> {lgf}")
                    x = cw//2 - lgs//2
                    y = lgy + lgs * i
                    draw.text((x, y), char, fill=lgc, font=font)
                    
            except Exception as e:
                print(f"绘制文字时出错: {e}")
        
        # 保存图像
        output_path = Path(f"{self.cid}.jpg")
        print(f"保存到 '{output_path}'！")
        cimg.save(output_path, 'JPEG', quality=95)
        print('-' * 60)
    
    def _draw_fish_top(self, draw, cw, fy, dy1, dy2, flc, flw, ftc, lcw, flm, iff):
        """绘制上鱼尾"""
        # 水平线
        draw.line([cw//2 - lcw//2, fy - flm, cw//2 + lcw//2, fy - flm], 
                 fill=flc, width=flw)
        
        # 鱼尾形状
        if dy1 > 0 or dy2 > 0:
            points = [
                (cw//2 - lcw//2, fy),
                (cw//2 + lcw//2, fy),
                (cw//2 + lcw//2, fy + dy1 + dy2),
                (cw//2, fy + dy1),
                (cw//2 - lcw//2, fy + dy1 + dy2)
            ]
            draw.polygon(points, fill=ftc, outline=flc, width=flw)
        
        # 下方连接线
        if not iff or (dy1 == 0 and dy2 == 0): #非花鱼尾或下鱼尾萎缩时，两细线萎缩为直线
            draw.line([cw//2 - lcw//2, fy + dy1 + dy2 + flm, cw//2, fy + dy1 + flm], 
                     fill=flc, width=1)
            draw.line([cw//2, fy + dy1 + flm, cw//2 + lcw//2, fy + dy1 + dy2 + flm], 
                     fill=flc, width=1)
    
    def _draw_fish_btm_down(self, draw, cw, fy, dy1, dy2, flc, flw, fbc, lcw, flm, iff):
        """绘制下鱼尾（向下）"""
        # 水平线
        draw.line([cw//2 - lcw//2, fy - flm, cw//2 + lcw//2, fy - flm], 
                 fill=flc, width=flw)
        
        # 鱼尾形状
        if dy1 > 0 or dy2 > 0:
            points = [
                (cw//2 - lcw//2, fy),
                (cw//2 + lcw//2, fy),
                (cw//2 + lcw//2, fy + dy1 + dy2),
                (cw//2, fy + dy1),
                (cw//2 - lcw//2, fy + dy1 + dy2)
            ]
            draw.polygon(points, fill=fbc, outline=flc, width=flw)
        if (not iff or (dy1 == 0 and dy2 == 0)): #非花鱼尾或下鱼尾萎缩时，两细线萎缩为直线
            draw.line([cw//2 - lcw//2, fy + dy1 + dy2 + flm, cw//2, fy + dy1 + flm], 
                    fill=flc, width=1)
            draw.line([cw//2, fy + dy1 + flm, cw//2 + lcw//2, fy + dy1 + dy2 + flm], 
                    fill=flc, width=1)
    
    def _draw_fish_btm_up(self, draw, cw, fy, dy1, dy2, flc, flw, fbc, lcw, flm, mt, mb, mov, iff):
        """绘制下鱼尾（向上）"""
        # 水平线
        draw.line([cw//2 - lcw//2, fy + flm, cw//2 + lcw//2, fy + flm], 
                 fill=flc, width=flw)
        
        # 鱼尾形状
        if dy1 > 0 or dy2 > 0:
            points = [
                (cw//2 - lcw//2, fy),
                (cw//2 + lcw//2, fy),
                (cw//2 + lcw//2, fy - dy1 - dy2),
                (cw//2, fy - dy1),
                (cw//2 - lcw//2, fy - dy1 - dy2)
            ]
            draw.polygon(points, fill=fbc, outline=flc, width=flw)
        
        if (not iff or (dy1 == 0 and dy2 == 0)): #非花鱼尾或下鱼尾萎缩时，两细线萎缩为直线
            draw.line([cw//2 - lcw//2, fy - dy1 - dy2 - flm, cw//2, fy - dy1 - flm], 
                    fill=flc, width=1)
            draw.line([cw//2, fy - dy1 - flm, cw//2 + lcw//2, fy - dy1 - dy2 - flm], 
                    fill=flc, width=1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='古籍刻本背景图生成工具')
    parser.add_argument('-c', '--config', required=True, 
                       help='配置文件ID（不含扩展名）')
    
    args = parser.parse_args()
    
    try:
        generator = CanvasGenerator(args.config)
        generator.create_canvas()
        
    except Exception as e:
        print(f"错误：{e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
