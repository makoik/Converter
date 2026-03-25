"""
Video & Audio Converter + Clip Merger
Built with PyQt6 + FFmpeg
Run: python converter.py
Requires: pip install PyQt6 | FFmpeg in system PATH
"""

import sys, os, re, shutil, subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QProgressBar, QFileDialog,
    QFrame, QSizePolicy, QScrollArea, QListWidget, QListWidgetItem,
    QAbstractItemView, QDoubleSpinBox, QTabWidget, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
from datetime import datetime

# ── Format Registry ──

VIDEO_FORMATS = {
    "MP4  (H.264)":    {"ext": "mp4",  "vcodec": "libx264",    "acodec": "aac"},
    "MP4  (H.265)":    {"ext": "mp4",  "vcodec": "libx265",    "acodec": "aac"},
    "MP4  (AV1)":      {"ext": "mp4",  "vcodec": "libaom-av1", "acodec": "aac"},
    "MP4  (copy)":     {"ext": "mp4",  "vcodec": "copy",       "acodec": "copy"},
    "MKV  (H.264)":    {"ext": "mkv",  "vcodec": "libx264",    "acodec": "aac"},
    "MKV  (H.265)":    {"ext": "mkv",  "vcodec": "libx265",    "acodec": "aac"},
    "MKV  (copy)":     {"ext": "mkv",  "vcodec": "copy",       "acodec": "copy"},
    "AVI  (xvid)":     {"ext": "avi",  "vcodec": "libxvid",    "acodec": "mp3"},
    "AVI  (copy)":     {"ext": "avi",  "vcodec": "copy",       "acodec": "copy"},
    "MOV  (H.264)":    {"ext": "mov",  "vcodec": "libx264",    "acodec": "aac"},
    "MOV  (copy)":     {"ext": "mov",  "vcodec": "copy",       "acodec": "copy"},
    "WebM (VP9)":      {"ext": "webm", "vcodec": "libvpx-vp9", "acodec": "libopus"},
    "WebM (VP8)":      {"ext": "webm", "vcodec": "libvpx",     "acodec": "libvorbis"},
    "WebM (copy)":     {"ext": "webm", "vcodec": "copy",       "acodec": "copy"},
    "FLV  (H.264)":    {"ext": "flv",  "vcodec": "libx264",    "acodec": "aac"},
    "WMV":             {"ext": "wmv",  "vcodec": "wmv2",       "acodec": "wmav2"},
    "GIF  (animated)": {"ext": "gif",  "vcodec": "gif",        "acodec": None},
    "TS   (MPEG-2)":   {"ext": "ts",   "vcodec": "mpeg2video", "acodec": "mp2"},
    "TS   (copy)":     {"ext": "ts",   "vcodec": "copy",       "acodec": "copy"},
}
AUDIO_FORMATS = {
    "MP3":  {"ext": "mp3",  "acodec": "libmp3lame"},
    "AAC":  {"ext": "aac",  "acodec": "aac"},
    "FLAC": {"ext": "flac", "acodec": "flac"},
    "WAV":  {"ext": "wav",  "acodec": "pcm_s16le"},
    "OGG":  {"ext": "ogg",  "acodec": "libvorbis"},
    "OPUS": {"ext": "opus", "acodec": "libopus"},
    "M4A":  {"ext": "m4a",  "acodec": "aac"},
    "WMA":  {"ext": "wma",  "acodec": "wmav2"},
}
QUALITY_PRESETS = {
    "Lossless / Best":          {"crf": "0",  "audio_bitrate": "320k"},
    "High (visually lossless)": {"crf": "18", "audio_bitrate": "256k"},
    "Medium (balanced)":        {"crf": "23", "audio_bitrate": "192k"},
    "Low (small file)":         {"crf": "28", "audio_bitrate": "128k"},
    "Very Low (tiny file)":     {"crf": "35", "audio_bitrate": "96k"},
}
RESOLUTION_PRESETS = {
    "Original":          None,
    "4K  (3840x2160)":   "3840:2160",
    "1440p (2560x1440)": "2560:1440",
    "1080p (1920x1080)": "1920:1080",
    "720p  (1280x720)":  "1280:720",
    "480p  (854x480)":   "854:480",
    "360p  (640x360)":   "640:360",
}

# ── Stylesheet ──

SS = """
* { font-family: 'JetBrains Mono', 'Courier New', monospace; color: #E8E0D0; }
QMainWindow, QWidget#root { background-color: #0F0F0F; }
QWidget { background-color: transparent; }
QScrollArea { border: none; background-color: #0F0F0F; }
QScrollBar:vertical { background: #1A1A1A; width: 6px; border-radius: 3px; }
QScrollBar::handle:vertical { background: #D97706; border-radius: 3px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QTabWidget::pane { border: 1px solid #1E1E1E; background-color: #0F0F0F; }
QTabBar::tab { background-color: #0F0F0F; color: #444444; padding: 8px 28px;
               font-size: 9px; letter-spacing: 3px; border: none;
               border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: #D97706; border-bottom: 2px solid #D97706; }
QTabBar::tab:hover { color: #E8E0D0; }
QFrame#dropzone { background-color: #141414; border: 2px dashed #2A2A2A; border-radius: 4px; }
QFrame#dropzone:hover { border-color: #D97706; background-color: #161410; }
QListWidget { background-color: #141414; border: 1px solid #222222; border-radius: 2px; outline: none; }
QListWidget::item { padding: 8px 12px; border-bottom: 1px solid #1E1E1E; font-size: 10px; }
QListWidget::item:selected { background-color: #1E1810; color: #D97706; border-left: 2px solid #D97706; }
QListWidget::item:hover { background-color: #1A1A1A; }
QLabel#section_title { color: #D97706; font-size: 9px; letter-spacing: 3px; font-weight: bold; }
QLabel#filename   { color: #E8E0D0; font-size: 13px; font-weight: bold; }
QLabel#meta       { color: #666666; font-size: 10px; }
QLabel#drop_hint  { color: #333333; font-size: 11px; letter-spacing: 1px; }
QLabel#drop_icon  { color: #2A2A2A; font-size: 40px; }
QLabel#status_ok  { color: #22C55E; font-size: 10px; letter-spacing: 1px; }
QLabel#status_err { color: #EF4444; font-size: 10px; letter-spacing: 1px; }
QLabel#status_info { color: #D97706; font-size: 10px; letter-spacing: 1px; }
QComboBox { background-color: #1A1A1A; border: 1px solid #2A2A2A; border-radius: 2px;
            padding: 6px 12px; font-size: 11px; color: #E8E0D0; min-width: 180px; }
QComboBox:focus { border-color: #D97706; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow { image: none; border-left: 4px solid transparent;
                        border-right: 4px solid transparent;
                        border-top: 5px solid #D97706; width: 0; height: 0; }
QComboBox QAbstractItemView { background-color: #1A1A1A; border: 1px solid #D97706;
                               selection-background-color: #D97706; selection-color: #0F0F0F; outline: none; }
QDoubleSpinBox { background-color: #1A1A1A; border: 1px solid #2A2A2A; border-radius: 2px;
                 padding: 5px 8px; font-size: 11px; color: #E8E0D0; min-width: 90px; }
QDoubleSpinBox:focus { border-color: #D97706; }
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { background-color: #2A2A2A; border: none; width: 16px; }
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover { background-color: #D97706; }
QPushButton#btn_primary { background-color: #D97706; color: #0F0F0F; border: none;
                          border-radius: 2px; padding: 10px 32px; font-size: 11px;
                          font-weight: bold; letter-spacing: 2px; }
QPushButton#btn_primary:hover    { background-color: #F59E0B; }
QPushButton#btn_primary:pressed  { background-color: #B45309; }
QPushButton#btn_primary:disabled { background-color: #2A2A2A; color: #444444; }
QPushButton#btn_secondary { background-color: transparent; color: #666666;
                            border: 1px solid #2A2A2A; border-radius: 2px;
                            padding: 8px 20px; font-size: 10px; letter-spacing: 1px; }
QPushButton#btn_secondary:hover { border-color: #D97706; color: #D97706; }
QPushButton#btn_danger { background-color: transparent; color: #666666;
                         border: 1px solid #2A2A2A; border-radius: 2px;
                         padding: 6px 14px; font-size: 10px; letter-spacing: 1px; }
QPushButton#btn_danger:hover { border-color: #EF4444; color: #EF4444; }
QPushButton#btn_cancel { background-color: transparent; color: #EF4444;
                         border: 1px solid #EF4444; border-radius: 2px;
                         padding: 8px 20px; font-size: 10px; letter-spacing: 1px; }
QPushButton#btn_cancel:hover { background-color: #EF4444; color: #0F0F0F; }
QProgressBar { background-color: #1A1A1A; border: none; border-radius: 2px; height: 4px; }
QProgressBar::chunk { background-color: #D97706; border-radius: 2px; }
QFrame#sep { background-color: #1E1E1E; max-height: 1px; }
"""

# ── Helpers ──

def make_sep():
    f = QFrame(); f.setObjectName("sep")
    f.setFrameShape(QFrame.Shape.HLine); f.setFixedHeight(1); return f

def stitle(t):
    l = QLabel(t); l.setObjectName("section_title"); return l

def probe_meta(path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration,size",
             "-show_entries", "stream=codec_name,width,height",
             "-of", "default=noprint_wrappers=1", path],
            capture_output=True, text=True, timeout=10)
        lines = {l.split("=")[0]: l.split("=")[1].strip()
                 for l in r.stdout.splitlines() if "=" in l}
        parts = []
        if "duration" in lines:
            d = float(lines["duration"]); parts.append(f"{int(d//60)}:{int(d%60):02d}")
        if "size" in lines:
            parts.append(f"{int(lines['size'])/1_048_576:.1f} MB")
        if "width" in lines and "height" in lines:
            parts.append(f"{lines['width']}x{lines['height']}")
        return "  |  ".join(parts)
    except Exception:
        return Path(path).suffix.upper().lstrip(".")

def probe_duration(path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=10)
        return float(r.stdout.strip())
    except Exception:
        return None


def probe_dimensions(path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height",
             "-of", "csv=p=0:s=x", path],
            capture_output=True, text=True, timeout=6)
        out = r.stdout.strip()
        if "x" in out:
            w, h = out.split("x")
            return int(w), int(h)
    except Exception:
        pass
    return None


def probe_streams(path):
    """Returns (has_video, has_audio) tuple for a file."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "stream=codec_type",
             "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=6)
        streams = [s.strip() for s in r.stdout.strip().split("\n") if s.strip()]
        has_v = any("video" in s for s in streams)
        has_a = any("audio" in s for s in streams)
        return has_v, has_a
    except Exception:
        return False, False


def probe_video_props(path):
    """Returns (width, height, fps) for a file or (None, None, None)."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,r_frame_rate",
             "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=6)
        parts = [p.strip() for p in r.stdout.strip().split(",")]
        if len(parts) >= 3:
            w, h, fps_str = parts[0], parts[1], parts[2]
            try:
                w, h = int(w), int(h)
                if "/" in fps_str:
                    num, den = fps_str.split("/")
                    fps = float(num) / float(den)
                else:
                    fps = float(fps_str)
                return w, h, fps
            except Exception:
                return None, None, None
    except Exception:
        pass
    return None, None, None


def log_error(msg):
    """Write error message to log file."""
    try:
        log_file = Path(Path.home()) / "forge_error.log"
        with open(log_file, "a") as f:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass

# ── Workers ──

class ConvertWorker(QThread):
    progress    = pyqtSignal(int)
    status_msg  = pyqtSignal(str)
    finished_ok = pyqtSignal(str)
    finished_err = pyqtSignal(str)

    def __init__(self, input_path, output_path, fmt_info, quality, resolution, is_audio=False):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.fmt_info = fmt_info
        self.quality = quality
        self.resolution = resolution
        self.is_audio = is_audio
        self._cancelled = False
        self._proc = None

    def cancel(self):
        self._cancelled = True
        if self._proc: self._proc.terminate()

    def run(self):
        dur = probe_duration(self.input_path)
        crf = self.quality["crf"]; abr = self.quality["audio_bitrate"]
        cmd = ["ffmpeg", "-y", "-i", self.input_path]

        if self.is_audio:
            cmd += ["-vn", "-c:a", self.fmt_info["acodec"], "-b:a", abr]
        else:
            vc = self.fmt_info["vcodec"]; ac = self.fmt_info.get("acodec")
            if vc == "copy":
                cmd += ["-c:v", "copy"]
            elif vc == "gif":
                pal = self.output_path + ".pal.png"
                subprocess.run(["ffmpeg", "-y", "-i", self.input_path, "-vf", "palettegen", pal],
                               capture_output=True)
                cmd = ["ffmpeg", "-y", "-i", self.input_path, "-i", pal,
                       "-lavfi", "paletteuse", self.output_path]
            else:
                cmd += ["-c:v", vc]
                if "vpx" in vc: cmd += ["-b:v", "0", "-crf", crf]
                elif vc not in ("mpeg2video", "wmv2", "libxvid"): cmd += ["-crf", crf]
                if self.resolution:
                    cmd += ["-vf", f"scale={self.resolution}:flags=lanczos"]
            if ac and ac != "copy" and vc != "gif": cmd += ["-c:a", ac, "-b:a", abr]
            elif ac == "copy": cmd += ["-c:a", "copy"]

        if "-lavfi" not in cmd:
            cmd += ["-progress", "pipe:1", "-nostats", self.output_path]
        self.status_msg.emit("CONVERTING...")
        self._exec(cmd, dur)

    def _exec(self, cmd, total_dur):
        try:
            self._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT, text=True, bufsize=1)
            pat = re.compile(r"out_time_ms=(\d+)")
            for line in self._proc.stdout:
                if self._cancelled: break
                m = pat.search(line)
                if m and total_dur:
                    self.progress.emit(min(int(int(m.group(1))/1_000_000/total_dur*100), 99))
            self._proc.wait()
            if self._cancelled:
                if os.path.exists(self.output_path): os.remove(self.output_path)
                self.finished_err.emit("Cancelled."); return
            if self._proc.returncode == 0:
                self.progress.emit(100); self.finished_ok.emit(self.output_path)
            else:
                err_output = self._proc.stdout.read() if self._proc.stdout else "Unknown error"
                self.finished_err.emit(err_output[-500:])
        except FileNotFoundError:
            self.finished_err.emit("ffmpeg not found in PATH.")
        except Exception as e:
            self.finished_err.emit(str(e))


class MergeWorker(QThread):
    progress    = pyqtSignal(int)
    status_msg  = pyqtSignal(str)
    finished_ok = pyqtSignal(str)
    finished_err = pyqtSignal(str)

    def __init__(self, clips, output_path, fmt_info, quality, resolution, fade_dur=0.4, fast_merge=False):
        super().__init__()
        self.clips = clips
        self.output_path = output_path
        self.fmt_info = fmt_info
        self.quality = quality
        self.resolution = resolution
        self.fade_dur = fade_dur
        self.fast_merge = fast_merge
        self._cancelled = False
        self._proc = None

    def cancel(self):
        self._cancelled = True
        if self._proc: self._proc.terminate()

    def run(self):
        if self.fast_merge:
            self._run_fast_merge()
        else:
            self._run_slow_merge()

    def _run_fast_merge(self):
        """Fast concat demuxer merge (no re-encoding, no fades)."""
        try:
            concat_file = self.output_path + ".txt"
            with open(concat_file, "w") as f:
                for clip in self.clips:
                    f.write(f"file '{os.path.abspath(clip)}'\n")
            self.status_msg.emit("CONCATENATING (NO RE-ENCODE)...")
            cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                   "-i", concat_file, "-c", "copy", self.output_path]
            self._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in self._proc.stdout:
                if self._cancelled: break
            self._proc.wait()
            if os.path.exists(concat_file):
                os.remove(concat_file)
            if self._cancelled:
                if os.path.exists(self.output_path): os.remove(self.output_path)
                self.finished_err.emit("Cancelled."); return
            if self._proc.returncode == 0:
                self.progress.emit(100); self.finished_ok.emit(self.output_path)
            else:
                self.finished_err.emit("Fast merge failed. Try merge with fades instead.")
        except Exception as e:
            self.finished_err.emit(str(e))

    def _run_slow_merge(self):
        """Slow merge with normalization and fades (requires re-encoding)."""
        self.status_msg.emit("PROBING CLIPS...")
        durations = []
        for i, c in enumerate(self.clips):
            d = probe_duration(c)
            if d is None:
                err = f"Could not probe duration: {Path(c).name}"
                log_error(err)
                self.finished_err.emit(err); return
            has_v, has_a = probe_streams(c)
            if not has_v:
                err = f"Clip {i+1} ({Path(c).name}) has no video stream"
                log_error(err)
                self.finished_err.emit(err); return
            durations.append((d, has_a))

        durations_list = [d for d, _ in durations]
        has_audio_list = [ha for _, ha in durations]
        has_any_audio = any(has_audio_list)
        
        # Verify consistency: all must have audio or all must not
        if not (all(has_audio_list) or not any(has_audio_list)):
            err = "All clips must have audio, or all must not have audio. Cannot mix."
            log_error(err)
            self.finished_err.emit(err); return
        
        total = sum(durations_list); fd = self.fade_dur; n = len(self.clips)
        vc = self.fmt_info["vcodec"]; ac = self.fmt_info.get("acodec")
        crf = self.quality.get("crf", "23"); abr = self.quality.get("audio_bitrate", "192k")

        inputs = []
        for c in self.clips: inputs += ["-i", c]

        # Probe first clip to get target resolution and frame rate
        ref_w, ref_h, ref_fps = probe_video_props(self.clips[0])
        if not ref_w or not ref_h:
            err = f"Could not probe video properties from {Path(self.clips[0]).name}"
            log_error(err)
            self.finished_err.emit(err); return

        # Normalize all clips to match first clip's resolution and frame rate
        filters = []
        for i, (dur, _) in enumerate(durations):
            fo = max(0.0, dur - fd)
            norm = f"scale={ref_w}:{ref_h}:flags=lanczos,fps={ref_fps}"
            filt = f"[{i}:v]{norm},fade=t=in:st=0:d={fd},fade=t=out:st={fo:.4f}:d={fd}[v{i}]"
            filters.append(filt)
        
        # Only add audio filters if clips have audio
        if has_any_audio:
            for i, (dur, _) in enumerate(durations):
                fo = max(0.0, dur - fd)
                filters.append(f"[{i}:a]afade=t=in:st=0:d={fd},afade=t=out:st={fo:.4f}:d={fd}[a{i}]")
            # concat input order: [v0][a0][v1][a1]... (interleaved video/audio pairs)
            concat_in = "".join(f"[v{i}][a{i}]" for i in range(n))
            filters.append(f"{concat_in}concat=n={n}:v=1:a=1[vout][aout]")
        else:
            # No audio: only video concat
            concat_in = "".join(f"[v{i}]" for i in range(n))
            filters.append(f"{concat_in}concat=n={n}:v=1:a=0[vout]")
        fg = ";".join(filters)

        if self.resolution:
            fg += f";[vout]scale={self.resolution}:flags=lanczos[vfinal]"
            vmap = "[vfinal]"
        else:
            vmap = "[vout]"

        cmd = ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", fg, "-map", vmap, "-c:v", vc,
        ]
        if has_any_audio:
            cmd += ["-map", "[aout]"]
        if "vpx" in vc:    cmd += ["-b:v", "0", "-crf", crf]
        elif vc not in ("copy", "mpeg2video", "wmv2", "libxvid", "gif"): cmd += ["-crf", crf]
        if ac and ac != "copy": cmd += ["-c:a", ac, "-b:a", abr]
        elif ac == "copy":      cmd += ["-c:a", "copy"]
        cmd += ["-progress", "pipe:1", "-nostats", self.output_path]

        self.status_msg.emit(f"MERGING {n} CLIPS...")
        try:
            self._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT, text=True, bufsize=1)
            pat = re.compile(r"out_time_ms=(\d+)")
            for line in self._proc.stdout:
                if self._cancelled: break
                m = pat.search(line)
                if m and total:
                    self.progress.emit(min(int(int(m.group(1))/1_000_000/total*100), 99))
            self._proc.wait()
            if self._cancelled:
                if os.path.exists(self.output_path): os.remove(self.output_path)
                self.finished_err.emit("Cancelled."); return
            if self._proc.returncode == 0:
                self.progress.emit(100); self.finished_ok.emit(self.output_path)
            else:
                err_output = self._proc.stdout.read() if self._proc.stdout else ""
                log_error(err_output)
                self.finished_err.emit(f"Merge failed. Check ~/forge_error.log for details. Last: {err_output[-300:]}")
        except FileNotFoundError:
            self.finished_err.emit("ffmpeg not found in PATH.")
        except Exception as e:
            self.finished_err.emit(str(e))

# ── Merge Optimization Helpers ──

def get_clip_codec_info(path):
    """Returns (vcodec, width, height, fps, acodec) for a clip or None if probe fails."""
    try:
        # Probe video codec, dimensions, fps
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name,width,height,r_frame_rate",
             "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=6)
        vparts = [p.strip() for p in r.stdout.strip().split(",")]
        if len(vparts) < 4:
            return None
        vcodec, width, height, fps_str = vparts[0], vparts[1], vparts[2], vparts[3]
        try:
            width, height = int(width), int(height)
            if "/" in fps_str:
                num, den = fps_str.split("/")
                fps = float(num) / float(den)
            else:
                fps = float(fps_str)
        except Exception:
            return None
        # Probe audio codec
        r_audio = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=codec_name",
             "-of", "csv=p=0:nokey=1", path],
            capture_output=True, text=True, timeout=6)
        acodec = r_audio.stdout.strip() if r_audio.stdout.strip() else None
        return vcodec, width, height, fps, acodec
    except Exception:
        return None

def clips_match_format(clips, target_vcodec, target_width, target_height, target_fps, target_acodec):
    """Check if all clips have matching codec/resolution/fps/acodec within tolerance."""
    try:
        fps_tolerance = 0.1  # Allow small FPS variations
        for clip in clips:
            info = get_clip_codec_info(clip)
            if info is None:
                return False
            vcodec, width, height, fps, acodec = info
            # Compare codecs and dimensions (case-insensitive for codec)
            if (vcodec.lower() != target_vcodec.lower() or
                width != target_width or height != target_height or
                abs(fps - target_fps) > fps_tolerance or
                (target_acodec and acodec and acodec.lower() != target_acodec.lower())):
                return False
        return True
    except Exception:
        return False

def get_format_for_copy_merge(clips):
    """Detect original format from clips and return matching copy codec format.
    Returns format dict if all clips share same extension and a copy variant exists,
    otherwise falls back to MKV (copy). Returns None only if clips list is empty.
    """
    if not clips:
        return None
    
    try:
        # Get extension from first clip
        first_ext = Path(clips[0]).suffix.lower().lstrip('.')
        if not first_ext:
            return VIDEO_FORMATS["MKV  (copy)"]
        
        # Check all clips have matching extension
        for clip in clips[1:]:
            clip_ext = Path(clip).suffix.lower().lstrip('.')
            if clip_ext != first_ext:
                # Extensions don't match, use MKV as safe fallback
                return VIDEO_FORMATS["MKV  (copy)"]
        
        # Find matching format with copy codec
        ext_format_map = {
            'mp4': 'MP4  (copy)',
            'mkv': 'MKV  (copy)',
            'avi': 'AVI  (copy)',
            'mov': 'MOV  (copy)',
            'webm': 'WebM (copy)',
            'ts': 'TS   (copy)',
        }
        
        format_key = ext_format_map.get(first_ext)
        if format_key and format_key in VIDEO_FORMATS:
            return VIDEO_FORMATS[format_key]
        
        # Extension not in supported list, use MKV as safe fallback
        return VIDEO_FORMATS["MKV  (copy)"]
    except Exception:
        # On any error, fall back to MKV
        return VIDEO_FORMATS["MKV  (copy)"]

# ── Drop Zones ──

class DropZone(QFrame):
    file_dropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropzone"); self.setAcceptDrops(True)
        self.setMinimumHeight(140); self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QVBoxLayout(self); lay.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.setSpacing(8)
        self.icon = QLabel("down"); self.icon.setObjectName("drop_icon")
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint = QLabel("DROP FILE HERE  |  OR CLICK TO BROWSE")
        self.hint.setObjectName("drop_hint"); self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fname = QLabel(""); self.fname.setObjectName("filename")
        self.fname.setAlignment(Qt.AlignmentFlag.AlignCenter); self.fname.setWordWrap(True); self.fname.hide()
        self.fmeta = QLabel(""); self.fmeta.setObjectName("meta")
        self.fmeta.setAlignment(Qt.AlignmentFlag.AlignCenter); self.fmeta.hide()
        lay.addWidget(self.icon); lay.addWidget(self.hint)
        lay.addWidget(self.fname); lay.addWidget(self.fmeta)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton: self._browse()

    def _browse(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select Media File", "",
            "Media Files (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.wmv *.ts "
            "*.mp3 *.aac *.flac *.wav *.ogg *.opus *.m4a *.wma);;All Files (*)")
        if p: self.file_dropped.emit(p)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.setStyleSheet("QFrame#dropzone{border-color:#D97706;background-color:#161410;}")

    def dragLeaveEvent(self, e): self.setStyleSheet("")

    def dropEvent(self, e):
        self.setStyleSheet("")
        urls = e.mimeData().urls()
        if urls: self.file_dropped.emit(urls[0].toLocalFile())

    def set_file(self, path, meta=""):
        n = Path(path).name; self.fname.setText(n[:47]+"..." if len(n)>50 else n)
        self.fmeta.setText(meta); self.icon.hide(); self.hint.hide()
        self.fname.show(); self.fmeta.show()

    def reset(self):
        self.icon.show(); self.hint.show(); self.fname.hide(); self.fmeta.hide()


class MultiDropZone(QFrame):
    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropzone"); self.setAcceptDrops(True)
        self.setMinimumHeight(72); self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QHBoxLayout(self); lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel("  +  DROP CLIPS HERE  |  OR CLICK TO ADD")
        lbl.setObjectName("drop_hint"); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            paths, _ = QFileDialog.getOpenFileNames(self, "Select Clips", "",
                "Video Files (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.wmv *.ts *.mpg);;All Files (*)")
            if paths: self.files_dropped.emit(paths)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.setStyleSheet("QFrame#dropzone{border-color:#D97706;background-color:#161410;}")

    def dragLeaveEvent(self, e): self.setStyleSheet("")

    def dropEvent(self, e):
        self.setStyleSheet("")
        paths = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        if paths: self.files_dropped.emit(paths)

# ── Reusable Settings Block And Mouse Wheel Disabler ──

class NoWheelQComboBox(QComboBox):
    def wheelEvent(self, event):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

class SettingsPanel(QWidget):
    def __init__(self, show_mode_toggle=True, parent=None):
        super().__init__(parent)
        self.mode = "video"
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(12)

        if show_mode_toggle:
            lay.addWidget(stitle("TYPE"))
            row = QHBoxLayout()
            self.btn_v = QPushButton("VIDEO"); self.btn_v.setObjectName("btn_primary")
            self.btn_v.clicked.connect(lambda: self._set_mode("video"))
            self.btn_a = QPushButton("AUDIO ONLY"); self.btn_a.setObjectName("btn_secondary")
            self.btn_a.clicked.connect(lambda: self._set_mode("audio"))
            row.addWidget(self.btn_v); row.addWidget(self.btn_a); row.addStretch()
            lay.addLayout(row); lay.addWidget(make_sep())
        else:
            self.btn_v = self.btn_a = None

        lay.addWidget(stitle("OUTPUT FORMAT"))
        self.fmt_combo = NoWheelQComboBox(); self.fmt_combo.setMinimumWidth(260)
        self.fmt_combo.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        for k in VIDEO_FORMATS: self.fmt_combo.addItem(k)
        lay.addWidget(self.fmt_combo); lay.addWidget(make_sep())

        lay.addWidget(stitle("QUALITY PRESET"))
        self.q_combo = NoWheelQComboBox()
        self.q_combo.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        for k in QUALITY_PRESETS: self.q_combo.addItem(k)
        self.q_combo.setCurrentIndex(2); lay.addWidget(self.q_combo)

        self.res_widget = QWidget()
        rl = QVBoxLayout(self.res_widget); rl.setContentsMargins(0,0,0,0); rl.setSpacing(8)
        rl.addWidget(make_sep()); rl.addWidget(stitle("RESOLUTION"))
        self.r_combo = NoWheelQComboBox()
        self.r_combo.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        for k in RESOLUTION_PRESETS: self.r_combo.addItem(k)
        rl.addWidget(self.r_combo)
        lay.addWidget(self.res_widget)

    def _set_mode(self, mode):
        self.mode = mode; self.fmt_combo.clear()
        if mode == "video":
            for k in VIDEO_FORMATS: self.fmt_combo.addItem(k)
            self.res_widget.setVisible(True)
            if self.btn_v:
                self.btn_v.setObjectName("btn_primary"); self.btn_a.setObjectName("btn_secondary")
        else:
            for k in AUDIO_FORMATS: self.fmt_combo.addItem(k)
            self.res_widget.setVisible(False)
            if self.btn_a:
                self.btn_a.setObjectName("btn_primary"); self.btn_v.setObjectName("btn_secondary")
        if self.btn_v:
            for b in (self.btn_v, self.btn_a):
                b.style().unpolish(b); b.style().polish(b)

    def get_fmt_info(self):
        lbl = self.fmt_combo.currentText()
        if self.mode == "audio": return AUDIO_FORMATS[lbl], True
        return VIDEO_FORMATS[lbl], False

    def get_quality(self):  return QUALITY_PRESETS[self.q_combo.currentText()]
    def get_resolution(self): return RESOLUTION_PRESETS.get(self.r_combo.currentText())

# ── Status helper ──

def set_status(lbl, msg, kind):
    obj = {"ok":"status_ok","err":"status_err","info":"status_info"}[kind]
    lbl.setObjectName(obj); lbl.setText(msg)
    lbl.style().unpolish(lbl); lbl.style().polish(lbl)

# ── Convert Tab ──
class ConvertTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.input_path = None; self.output_dir = None; self.worker = None

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget(); content.setObjectName("root")
        lay = QVBoxLayout(content); lay.setContentsMargins(24,24,24,24); lay.setSpacing(14)

        lay.addWidget(stitle("INPUT FILE"))
        self.drop = DropZone(); self.drop.file_dropped.connect(self._on_file)
        lay.addWidget(self.drop); lay.addWidget(make_sep())

        self.settings = SettingsPanel(show_mode_toggle=True)
        lay.addWidget(self.settings); lay.addWidget(make_sep())

        lay.addWidget(stitle("OUTPUT FOLDER"))
        out_row = QHBoxLayout()
        self.out_lbl = QLabel("Same as input file"); self.out_lbl.setObjectName("meta")
        self.out_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        btn_dir = QPushButton("CHANGE"); btn_dir.setObjectName("btn_secondary")
        btn_dir.clicked.connect(self._choose_dir)
        out_row.addWidget(self.out_lbl); out_row.addWidget(btn_dir)
        lay.addLayout(out_row); lay.addWidget(make_sep())

        act = QHBoxLayout()
        self.btn_go = QPushButton("CONVERT"); self.btn_go.setObjectName("btn_primary")
        self.btn_go.setEnabled(False); self.btn_go.clicked.connect(self._start)
        self.btn_cl = QPushButton("CLEAR"); self.btn_cl.setObjectName("btn_secondary")
        self.btn_cl.clicked.connect(self._clear)
        self.btn_cx = QPushButton("CANCEL"); self.btn_cx.setObjectName("btn_cancel")
        self.btn_cx.setVisible(False); self.btn_cx.clicked.connect(self._cancel)
        act.addWidget(self.btn_go); act.addWidget(self.btn_cl); act.addWidget(self.btn_cx); act.addStretch()
        lay.addLayout(act)

        self.pbar = QProgressBar(); self.pbar.setValue(0); self.pbar.setFixedHeight(4); self.pbar.setVisible(False)
        lay.addWidget(self.pbar)
        self.slbl = QLabel(""); self.slbl.setObjectName("status_info"); self.slbl.setWordWrap(True)
        lay.addWidget(self.slbl); lay.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        outer.addWidget(scroll)

        # Bottom footer with open folder button
        footer = QHBoxLayout(); footer.addStretch()
        self.btn_open = QPushButton("OPEN FOLDER"); self.btn_open.setObjectName("btn_secondary")
        self.btn_open.setMaximumWidth(120); self.btn_open.clicked.connect(self._open_folder)
        footer.addWidget(self.btn_open); footer.setContentsMargins(24, 8, 24, 8)
        footer_widget = QWidget(); footer_widget.setLayout(footer); footer_widget.setMaximumHeight(44)
        outer.addWidget(footer_widget)

    def _on_file(self, p):
        self.input_path = p; self.drop.set_file(p, probe_meta(p))
        self.btn_go.setEnabled(True); self.slbl.setText("")

    def _choose_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if d: self.output_dir = d; self.out_lbl.setText(d)

    def _start(self):
        if not self.input_path: return
        fmt_info, is_audio = self.settings.get_fmt_info()
        quality = self.settings.get_quality()
        # Only apply a target resolution if the input is larger than the target.
        selected_res = self.settings.get_resolution() if not is_audio else None
        resolution = None
        if selected_res and not is_audio:
            dims = probe_dimensions(self.input_path)
            if dims:
                iw, ih = dims
                try:
                    tw, th = map(int, selected_res.split(":"))
                    if iw > tw or ih > th:
                        resolution = selected_res
                except Exception:
                    resolution = selected_res
            else:
                # Could not probe dimensions; apply requested resolution conservatively
                resolution = selected_res
        ext = fmt_info["ext"]
        src = Path(self.input_path)
        out_dir = Path(self.output_dir) if self.output_dir else src.parent
        out = str(out_dir / f"{src.stem}_converted.{ext}")
        if Path(out).resolve() == src.resolve(): out = str(out_dir / f"{src.stem}_conv.{ext}")
        self.btn_go.setEnabled(False); self.btn_cl.setEnabled(False)
        self.btn_cx.setVisible(True); self.pbar.setVisible(True); self.pbar.setValue(0)
        set_status(self.slbl, "PREPARING...", "info")
        self.worker = ConvertWorker(self.input_path, out, fmt_info, quality, resolution, is_audio)
        self.worker.progress.connect(self.pbar.setValue)
        self.worker.status_msg.connect(lambda m: set_status(self.slbl, m, "info"))
        self.worker.finished_ok.connect(self._ok); self.worker.finished_err.connect(self._err)
        self.worker.start()

    def _cancel(self):
        if self.worker: self.worker.cancel()

    def _ok(self, p):
        self.pbar.setValue(100); set_status(self.slbl, f"DONE  ->  {Path(p).name}", "ok"); self._reset()

    def _err(self, e):
        self.pbar.setValue(0); set_status(self.slbl, f"ERROR  {e}", "err"); self._reset()

    def _reset(self):
        self.btn_go.setEnabled(True); self.btn_cl.setEnabled(True); self.btn_cx.setVisible(False)

    def _clear(self):
        self.input_path = None; self.drop.reset(); self.btn_go.setEnabled(False)
        self.pbar.setValue(0); self.pbar.setVisible(False); self.slbl.setText(""); self.btn_cx.setVisible(False)

    def _open_folder(self):
        out_dir = Path(self.output_dir) if self.output_dir else Path(self.input_path).parent if self.input_path else None
        if out_dir and out_dir.exists():
            os.startfile(str(out_dir))

# ── Merge Tab ──

class MergeTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clips = []; self.output_dir = None; self.worker = None

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget(); content.setObjectName("root")
        lay = QVBoxLayout(content); lay.setContentsMargins(24,24,24,24); lay.setSpacing(14)

        lay.addWidget(stitle("ADD CLIPS"))
        self.mdrop = MultiDropZone(); self.mdrop.files_dropped.connect(self._add_clips)
        lay.addWidget(self.mdrop)

        list_hdr = QHBoxLayout()
        list_hdr.addWidget(stitle("CLIP ORDER  (drag to reorder)"))
        list_hdr.addStretch()
        btn_rm = QPushButton("REMOVE SELECTED"); btn_rm.setObjectName("btn_danger")
        btn_rm.clicked.connect(self._remove_selected)
        btn_clr = QPushButton("CLEAR ALL"); btn_clr.setObjectName("btn_danger")
        btn_clr.clicked.connect(self._clear_clips)
        list_hdr.addWidget(btn_rm); list_hdr.addWidget(btn_clr)
        lay.addLayout(list_hdr)

        self.clip_list = QListWidget()
        self.clip_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.clip_list.setMinimumHeight(160); self.clip_list.setMaximumHeight(220)
        self.clip_list.model().rowsMoved.connect(self._sync_order)
        lay.addWidget(self.clip_list); lay.addWidget(make_sep())

        fade_row = QHBoxLayout()
        fade_row.addWidget(stitle("FADE DURATION"))
        self.fade_spin = QDoubleSpinBox()
        self.fade_spin.setRange(0.1, 2.0); self.fade_spin.setSingleStep(0.1)
        self.fade_spin.setValue(0.4); self.fade_spin.setSuffix("  sec")
        fade_row.addWidget(self.fade_spin)
        fade_row.addSpacing(12)
        hint = QLabel("fade-to-black between clips"); hint.setObjectName("meta")
        fade_row.addWidget(hint); fade_row.addStretch()
        lay.addLayout(fade_row); lay.addWidget(make_sep())

        # Quick Merge toggle
        qm_row = QHBoxLayout()
        qm_row.addWidget(stitle("QUICK MERGE"))
        self.qm_toggle = QPushButton("OFF"); self.qm_toggle.setObjectName("btn_secondary")
        self.qm_toggle.setMaximumWidth(60); self.qm_toggle.clicked.connect(self._toggle_quick_merge)
        qm_row.addWidget(self.qm_toggle); qm_row.addSpacing(16)
        self.qm_warn = QLabel("Uses first clip's properties. All clips must be identical."); self.qm_warn.setObjectName("meta")
        self.qm_warn.setVisible(False); qm_row.addWidget(self.qm_warn); qm_row.addStretch()
        lay.addLayout(qm_row); lay.addWidget(make_sep())
        self.quick_merge_enabled = False

        self.settings = SettingsPanel(show_mode_toggle=False)
        lay.addWidget(self.settings); lay.addWidget(make_sep())

        lay.addWidget(stitle("OUTPUT FOLDER"))
        out_row = QHBoxLayout()
        self.out_lbl = QLabel("Same as first clip"); self.out_lbl.setObjectName("meta")
        self.out_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        btn_dir = QPushButton("CHANGE"); btn_dir.setObjectName("btn_secondary")
        btn_dir.clicked.connect(self._choose_dir)
        out_row.addWidget(self.out_lbl); out_row.addWidget(btn_dir)
        lay.addLayout(out_row); lay.addWidget(make_sep())

        act = QHBoxLayout()
        self.btn_go = QPushButton("MERGE + CONVERT"); self.btn_go.setObjectName("btn_primary")
        self.btn_go.setEnabled(False); self.btn_go.clicked.connect(self._start)
        self.btn_cx = QPushButton("CANCEL"); self.btn_cx.setObjectName("btn_cancel")
        self.btn_cx.setVisible(False); self.btn_cx.clicked.connect(self._cancel)
        act.addWidget(self.btn_go); act.addWidget(self.btn_cx); act.addStretch()
        lay.addLayout(act)

        self.pbar = QProgressBar(); self.pbar.setValue(0); self.pbar.setFixedHeight(4); self.pbar.setVisible(False)
        lay.addWidget(self.pbar)
        self.slbl = QLabel(""); self.slbl.setObjectName("status_info"); self.slbl.setWordWrap(True)
        lay.addWidget(self.slbl); lay.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        outer.addWidget(scroll)

        # Bottom footer with open folder button
        footer = QHBoxLayout(); footer.addStretch()
        self.btn_open = QPushButton("OPEN FOLDER"); self.btn_open.setObjectName("btn_secondary")
        self.btn_open.setMaximumWidth(120); self.btn_open.clicked.connect(self._open_folder)
        footer.addWidget(self.btn_open); footer.setContentsMargins(24, 8, 24, 8)
        footer_widget = QWidget(); footer_widget.setLayout(footer); footer_widget.setMaximumHeight(44)
        outer.addWidget(footer_widget)

    def _add_clips(self, paths):
        for p in paths:
            if p not in self.clips:
                self.clips.append(p)
                n = Path(p).name; meta = probe_meta(p)
                item = QListWidgetItem(f"  {len(self.clips):02d}  {n}   [{meta}]")
                item.setData(Qt.ItemDataRole.UserRole, p)
                self.clip_list.addItem(item)
        self._update_btn()

    def _sync_order(self):
        self.clips = []
        for i in range(self.clip_list.count()):
            item = self.clip_list.item(i)
            p = item.data(Qt.ItemDataRole.UserRole); self.clips.append(p)
            n = Path(p).name; item.setText(f"  {i+1:02d}  {n}   [{probe_meta(p)}]")

    def _remove_selected(self):
        for item in self.clip_list.selectedItems():
            p = item.data(Qt.ItemDataRole.UserRole)
            if p in self.clips: self.clips.remove(p)
            self.clip_list.takeItem(self.clip_list.row(item))
        self._sync_order(); self._update_btn()

    def _clear_clips(self):
        self.clips.clear(); self.clip_list.clear(); self._update_btn()

    def _update_btn(self): self.btn_go.setEnabled(len(self.clips) >= 2)

    def _toggle_quick_merge(self):
        self.quick_merge_enabled = not self.quick_merge_enabled
        if self.quick_merge_enabled:
            self.qm_toggle.setText("ON"); self.qm_toggle.setObjectName("btn_primary")
            self.qm_warn.setVisible(True)
        else:
            self.qm_toggle.setText("OFF"); self.qm_toggle.setObjectName("btn_secondary")
            self.qm_warn.setVisible(False)
        self.qm_toggle.style().unpolish(self.qm_toggle); self.qm_toggle.style().polish(self.qm_toggle)

    def _choose_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if d: self.output_dir = d; self.out_lbl.setText(d)

    def _start(self):
        if len(self.clips) < 2: return
        
        fast_merge = False
        resolution = None
        
        if self.quick_merge_enabled:
            # Quick merge mode: auto-detect from first clip and validate all match
            first_info = get_clip_codec_info(self.clips[0])
            if not first_info:
                set_status(self.slbl, "ERROR Could not probe first clip properties", "err")
                return
            
            vcodec, width, height, fps, acodec = first_info
            
            # Validate all clips match
            if not clips_match_format(self.clips, vcodec, width, height, fps, acodec):
                QMessageBox.warning(self, "Clips Not Compatible",
                    "Not all clips have identical properties.\n\n"
                    "Quick Merge requires all clips to match:\n"
                    "• Codec • Resolution • Frame rate • Audio codec\n\n"
                    "Turn off Quick Merge to use merge with format conversion, or ensure all clips are identical.")
                return
            
            fast_merge = True
            fmt_info = get_format_for_copy_merge(self.clips)  # Preserve original format if possible
            quality = {}
        else:
            # Normal merge mode: use settings panel format
            fmt_info, _ = self.settings.get_fmt_info()
            quality = self.settings.get_quality()
            selected_res = self.settings.get_resolution()
            if selected_res:
                dims = probe_dimensions(self.clips[0])
                if dims:
                    iw, ih = dims
                    try:
                        tw, th = map(int, selected_res.split(":"))
                        if iw > tw or ih > th:
                            resolution = selected_res
                    except Exception:
                        resolution = selected_res
                else:
                    resolution = selected_res
        
        ext = fmt_info["ext"]; fade_dur = self.fade_spin.value()
        out_dir = Path(self.output_dir) if self.output_dir else Path(self.clips[0]).parent
        out = str(out_dir / f"welder_merged.{ext}")
        
        self.btn_go.setEnabled(False); self.btn_cx.setVisible(True)
        self.pbar.setVisible(True); self.pbar.setValue(0)
        set_status(self.slbl, "PREPARING...", "info")
        self.worker = MergeWorker(list(self.clips), out, fmt_info, quality, resolution, fade_dur, fast_merge)
        self.worker.progress.connect(self.pbar.setValue)
        self.worker.status_msg.connect(lambda m: set_status(self.slbl, m, "info"))
        self.worker.finished_ok.connect(self._ok); self.worker.finished_err.connect(self._err)
        self.worker.start()

    def _cancel(self):
        if self.worker: self.worker.cancel()

    def _ok(self, p):
        self.pbar.setValue(100); set_status(self.slbl, f"DONE  ->  {Path(p).name}", "ok"); self._reset()

    def _err(self, e):
        self.pbar.setValue(0); set_status(self.slbl, f"ERROR  {e}", "err"); self._reset()

    def _reset(self): self._update_btn(); self.btn_cx.setVisible(False)

    def _open_folder(self):
        out_dir = Path(self.output_dir) if self.output_dir else Path(self.clips[0]).parent if self.clips else None
        if out_dir and out_dir.exists():
            os.startfile(str(out_dir))

# ── Main Window ───────────────────────────────────────────────────────────────

class ForgeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VideoWelder - Media Merger")
        self.setMinimumSize(640, 720); self.resize(680, 800)
        self._build(); self._check_ffmpeg()

    def _build(self):
        root = QWidget(); root.setObjectName("root"); self.setCentralWidget(root)
        outer = QVBoxLayout(root); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)

        hdr = QWidget(); hdr.setStyleSheet("background-color:#0A0A0A;border-bottom:1px solid #1A1A1A;")
        hdr.setFixedHeight(52); hl = QHBoxLayout(hdr); hl.setContentsMargins(24,0,24,0)
        t1 = QLabel("VideoWelder"); t1.setStyleSheet("color:#D97706;font-size:14px;font-weight:bold;letter-spacing:4px;")
        t2 = QLabel("MEDIA CONVERTER"); t2.setStyleSheet("color:#333333;font-size:9px;letter-spacing:3px;")
        self.badge = QLabel("CHECKING..."); self.badge.setObjectName("status_info")
        self.badge.setAlignment(Qt.AlignmentFlag.AlignRight)
        hl.addWidget(t1); hl.addSpacing(12); hl.addWidget(t2); hl.addStretch(); hl.addWidget(self.badge)
        outer.addWidget(hdr)

        self.tabs = QTabWidget(); self.tabs.setDocumentMode(True)
        self.tabs.addTab(ConvertTab(), "CONVERT")
        self.tabs.addTab(MergeTab(),   "MERGE + FADE")
        outer.addWidget(self.tabs)

        ftr = QWidget(); ftr.setStyleSheet("background-color:#0A0A0A;border-top:1px solid #1A1A1A;")
        ftr.setFixedHeight(28); fl = QHBoxLayout(ftr); fl.setContentsMargins(24,0,24,0)
        fb = QLabel("VideoWelder  |  POWERED BY FFMPEG"); fb.setStyleSheet("color:#2A2A2A;font-size:8px;letter-spacing:2px;")
        fl.addStretch(); fl.addWidget(fb); outer.addWidget(ftr)

    def _check_ffmpeg(self):
        if shutil.which("ffmpeg") and shutil.which("ffprobe"):
            try:
                r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
                line = r.stdout.splitlines()[0] if r.stdout else ""
                ver = line.split("version")[1].strip().split(" ")[0] if "version" in line else ""
                self.badge.setText(f"FFMPEG {ver}"); self.badge.setObjectName("status_ok")
            except Exception:
                self.badge.setText("FFMPEG OK"); self.badge.setObjectName("status_ok")
        else:
            self.badge.setText("FFMPEG NOT FOUND"); self.badge.setObjectName("status_err")
        self.badge.style().unpolish(self.badge); self.badge.style().polish(self.badge)

# ── Entry Point ──

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(SS); app.setApplicationName("VideoWelder")
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,          QColor("#0F0F0F"))
    pal.setColor(QPalette.ColorRole.WindowText,      QColor("#E8E0D0"))
    pal.setColor(QPalette.ColorRole.Base,            QColor("#141414"))
    pal.setColor(QPalette.ColorRole.Text,            QColor("#E8E0D0"))
    pal.setColor(QPalette.ColorRole.Button,          QColor("#1A1A1A"))
    pal.setColor(QPalette.ColorRole.ButtonText,      QColor("#E8E0D0"))
    pal.setColor(QPalette.ColorRole.Highlight,       QColor("#D97706"))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#0F0F0F"))
    app.setPalette(pal)
    w = ForgeWindow(); w.show(); sys.exit(app.exec())
