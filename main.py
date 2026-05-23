"""
Language Translation Tool
Requirements: deep-translator, pyperclip, gtts, pygame
Run: python main.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
from deep_translator import GoogleTranslator
import pyperclip
from gtts import gTTS
import pygame
import os
import threading
import time

# ─────────────────────────────────────────────────────────
#  LANGUAGE DATA
# ─────────────────────────────────────────────────────────

LANGUAGE_DICT = {
    'Auto Detect':         'auto',
    'English':             'en',
    'Urdu':                'ur',
    'Hindi':               'hi',
    'French':              'fr',
    'Spanish':             'es',
    'German':              'de',
    'Italian':             'it',
    'Portuguese':          'pt',
    'Russian':             'ru',
    'Chinese (Simplified)':'zh-CN',
    'Japanese':            'ja',
    'Korean':              'ko',
    'Arabic':              'ar',
    'Turkish':             'tr',
    'Bengali':             'bn',
    'Punjabi':             'pa',
    'Tamil':               'ta',
    'Telugu':              'te',
    'Malayalam':           'ml',
    'Thai':                'th',
    'Vietnamese':          'vi',
    'Dutch':               'nl',
    'Greek':               'el',
    'Polish':              'pl',
}

# gTTS needs slightly different codes for some languages
GTTS_CODE_MAP = {
    'zh-CN': 'zh',
    'pa':    'en',   # gTTS has limited Punjabi support; fallback to en
}

LANGUAGE_NAMES = ['Auto Detect'] + sorted(k for k in LANGUAGE_DICT if k != 'Auto Detect')

# ─────────────────────────────────────────────────────────
#  THEME COLOURS
# ─────────────────────────────────────────────────────────

C = {
    'bg':        '#0f0f1a',
    'panel':     '#1a1a2e',
    'card':      '#16213e',
    'input_bg':  '#0f3460',
    'accent':    '#e94560',
    'accent2':   '#533483',
    'btn_green': '#0f9b58',
    'btn_blue':  '#1565c0',
    'btn_orange':'#e65100',
    'btn_hover_g':'#0d8a4e',
    'btn_hover_b':'#1255a8',
    'btn_hover_o':'#cc4700',
    'text':      '#e8eaf6',
    'text_dim':  '#9e9eb5',
    'text_input':'#e8f4f8',
    'border':    '#2a2a4a',
    'status_ok': '#00e676',
    'status_err':'#ff5252',
    'white':     '#ffffff',
}

# ─────────────────────────────────────────────────────────
#  APP CLASS
# ─────────────────────────────────────────────────────────

class TranslatorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._setup_window()
        self._init_pygame()
        self._build_ui()

    # ── Window Setup ─────────────────────────────────────
    def _setup_window(self):
        self.root.title("🌍 Language Translator")
        self.root.geometry("860x720")
        self.root.minsize(700, 600)
        self.root.config(bg=C['bg'])
        self.root.resizable(True, True)

        # Center window on screen
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x  = (sw - 860) // 2
        y  = (sh - 720) // 2
        self.root.geometry(f"860x720+{x}+{y}")

    def _init_pygame(self):
        try:
            pygame.mixer.init()
            self._pygame_ok = True
        except Exception:
            self._pygame_ok = False

    # ── UI Construction ───────────────────────────────────
    def _build_ui(self):
        # ── Title bar ──────────────────────────────────
        title_frame = tk.Frame(self.root, bg=C['panel'], pady=18)
        title_frame.pack(fill='x')

        tk.Label(
            title_frame,
            text="🌍  Language Translator",
            font=("Segoe UI", 22, "bold"),
            bg=C['panel'],
            fg=C['white']
        ).pack()

        tk.Label(
            title_frame,
            text="Translate text instantly into 25+ languages",
            font=("Segoe UI", 10),
            bg=C['panel'],
            fg=C['text_dim']
        ).pack(pady=(2, 0))

        # ── Main content area ─────────────────────────
        content = tk.Frame(self.root, bg=C['bg'])
        content.pack(fill='both', expand=True, padx=24, pady=16)

        # ── Language selector row ─────────────────────
        lang_card = tk.Frame(content, bg=C['card'],
                             highlightbackground=C['border'],
                             highlightthickness=1)
        lang_card.pack(fill='x', pady=(0, 12))

        inner_lang = tk.Frame(lang_card, bg=C['card'], padx=20, pady=14)
        inner_lang.pack(fill='x')
        inner_lang.columnconfigure(0, weight=1)
        inner_lang.columnconfigure(2, weight=1)

        # Source language
        self._combo_label(inner_lang, "Source Language", 0)
        self.source_var = tk.StringVar(value="Auto Detect")
        self.source_combo = self._make_combo(inner_lang, self.source_var, 1)

        # Swap button
        swap_btn = tk.Button(
            inner_lang,
            text="⇄",
            font=("Segoe UI", 16, "bold"),
            bg=C['accent2'],
            fg=C['white'],
            relief='flat',
            bd=0,
            padx=12,
            pady=4,
            cursor='hand2',
            command=self._swap_languages,
            activebackground='#6a44a3',
            activeforeground=C['white']
        )
        swap_btn.grid(row=0, column=1, rowspan=2, padx=14, pady=4)

        # Target language
        self._combo_label(inner_lang, "Target Language", 2)
        self.target_var = tk.StringVar(value="Urdu")
        self.target_combo = self._make_combo(inner_lang, self.target_var, 3)

        # ── Input box ─────────────────────────────────
        self._section_label(content, "✏️  Enter Text")
        in_card = tk.Frame(content, bg=C['input_bg'],
                           highlightbackground=C['accent'],
                           highlightthickness=1)
        in_card.pack(fill='x', pady=(2, 12))

        self.text_input = tk.Text(
            in_card,
            height=7,
            font=("Segoe UI", 12),
            wrap='word',
            bg=C['input_bg'],
            fg=C['text_input'],
            insertbackground=C['white'],
            relief='flat',
            padx=14,
            pady=10,
            bd=0,
        )
        self.text_input.pack(fill='x', padx=2, pady=2)

        # Char counter
        self.char_var = tk.StringVar(value="0 / 5000 characters")
        tk.Label(
            in_card,
            textvariable=self.char_var,
            font=("Segoe UI", 9),
            bg=C['input_bg'],
            fg=C['text_dim'],
            anchor='e'
        ).pack(fill='x', padx=14, pady=(0, 6))
        self.text_input.bind('<KeyRelease>', self._update_char_count)

        # ── Action buttons ────────────────────────────
        btn_frame = tk.Frame(content, bg=C['bg'])
        btn_frame.pack(fill='x', pady=(0, 12))

        self._make_btn(btn_frame, "🔁  Translate", C['btn_green'],
                       C['btn_hover_g'], self._translate, side='left')
        self._make_btn(btn_frame, "📋  Copy", C['btn_blue'],
                       C['btn_hover_b'], self._copy, side='left')
        self._make_btn(btn_frame, "🔊  Speak", C['btn_orange'],
                       C['btn_hover_o'], self._speak, side='left')
        self._make_btn(btn_frame, "🗑️  Clear", C['panel'],
                       '#2a2a4a', self._clear, side='right')

        # Keyboard shortcut hint
        tk.Label(
            btn_frame,
            text="Ctrl+Enter to translate",
            font=("Segoe UI", 9),
            bg=C['bg'],
            fg=C['text_dim']
        ).pack(side='right', padx=8)
        self.root.bind('<Control-Return>', lambda e: self._translate())

        # ── Output box ────────────────────────────────
        self._section_label(content, "🌐  Translation")
        out_card = tk.Frame(content, bg=C['card'],
                            highlightbackground=C['border'],
                            highlightthickness=1)
        out_card.pack(fill='both', expand=True, pady=(2, 8))

        self.text_output = tk.Text(
            out_card,
            font=("Segoe UI", 12),
            wrap='word',
            bg=C['card'],
            fg=C['text'],
            insertbackground=C['white'],
            relief='flat',
            padx=14,
            pady=10,
            bd=0,
            state='disabled',
        )
        scroll = ttk.Scrollbar(out_card, command=self.text_output.yview)
        self.text_output.config(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.text_output.pack(fill='both', expand=True, padx=2, pady=2)

        # ── Status bar ────────────────────────────────
        self.status_var = tk.StringVar(value="Ready  •  Enter text and press Translate")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
            bg=C['panel'],
            fg=C['text_dim'],
            anchor='w',
            padx=16,
            pady=6
        )
        status_bar.pack(fill='x', side='bottom')
        self.status_label = status_bar

    # ── Helper widget builders ───────────────────────────
    def _section_label(self, parent, text):
        tk.Label(
            parent,
            text=text,
            font=("Segoe UI", 11, "bold"),
            bg=C['bg'],
            fg=C['text_dim'],
            anchor='w'
        ).pack(fill='x', pady=(4, 2))

    def _combo_label(self, parent, text, col):
        tk.Label(
            parent,
            text=text,
            font=("Segoe UI", 10, "bold"),
            bg=C['card'],
            fg=C['text_dim']
        ).grid(row=0, column=col, sticky='w', padx=(0, 4))

    def _make_combo(self, parent, var, col):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'Dark.TCombobox',
            fieldbackground=C['input_bg'],
            background=C['input_bg'],
            foreground=C['text'],
            arrowcolor=C['text'],
            bordercolor=C['border'],
            lightcolor=C['border'],
            darkcolor=C['border'],
            insertcolor=C['white'],
        )
        style.map('Dark.TCombobox',
                  fieldbackground=[('readonly', C['input_bg'])],
                  foreground=[('readonly', C['text'])])

        cb = ttk.Combobox(
            parent,
            textvariable=var,
            values=LANGUAGE_NAMES,
            width=26,
            state='readonly',
            style='Dark.TCombobox',
            font=("Segoe UI", 11),
        )
        cb.grid(row=1, column=col, sticky='ew', padx=(0, 4), pady=(4, 0))
        return cb

    def _make_btn(self, parent, text, color, hover_color, cmd, side='left'):
        btn = tk.Button(
            parent,
            text=text,
            command=cmd,
            font=("Segoe UI", 11, "bold"),
            bg=color,
            fg=C['white'],
            relief='flat',
            bd=0,
            padx=18,
            pady=8,
            cursor='hand2',
            activebackground=hover_color,
            activeforeground=C['white'],
        )
        btn.pack(side=side, padx=(0, 8))

        def on_enter(e):  btn.config(bg=hover_color)
        def on_leave(e):  btn.config(bg=color)
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        return btn

    # ── Logic Functions ──────────────────────────────────
    def _update_char_count(self, event=None):
        n = len(self.text_input.get("1.0", "end-1c"))
        self.char_var.set(f"{n} / 5000 characters")

    def _set_status(self, msg, color=None):
        self.status_var.set(msg)
        self.status_label.config(fg=color or C['text_dim'])

    def _set_output(self, text):
        self.text_output.config(state='normal')
        self.text_output.delete("1.0", tk.END)
        self.text_output.insert(tk.END, text)
        self.text_output.config(state='disabled')

    def _get_output(self):
        return self.text_output.get("1.0", tk.END).strip()

    def _translate(self):
        input_text = self.text_input.get("1.0", tk.END).strip()
        if not input_text:
            self._set_status("⚠  Please enter text to translate.", C['status_err'])
            return

        if len(input_text) > 5000:
            self._set_status("⚠  Text is too long (max 5000 characters).", C['status_err'])
            return

        src_name = self.source_var.get()
        tgt_name = self.target_var.get()

        if tgt_name == 'Auto Detect':
            self._set_status("⚠  Please select a real target language.", C['status_err'])
            return

        src_code = LANGUAGE_DICT.get(src_name, 'auto')
        tgt_code = LANGUAGE_DICT.get(tgt_name, 'en')

        self._set_status("⏳  Translating…", C['text_dim'])
        self.root.update_idletasks()

        try:
            result = GoogleTranslator(source=src_code, target=tgt_code).translate(input_text)
            if not result:
                raise ValueError("Empty result returned.")
            self._set_output(result)
            self._set_status(
                f"✓  Translated {len(input_text)} chars  •  {src_name} → {tgt_name}",
                C['status_ok']
            )
        except Exception as e:
            self._set_status(f"✗  Translation failed: {e}", C['status_err'])
            messagebox.showerror("Translation Error", str(e))

    def _copy(self):
        text = self._get_output()
        if not text:
            self._set_status("⚠  Nothing to copy yet.", C['status_err'])
            return
        try:
            pyperclip.copy(text)
            self._set_status("✓  Translated text copied to clipboard!", C['status_ok'])
        except Exception as e:
            self._set_status(f"✗  Copy failed: {e}", C['status_err'])

    def _speak(self):
        text = self._get_output()
        if not text:
            self._set_status("⚠  No translated text to speak.", C['status_err'])
            return

        tgt_name = self.target_var.get()
        lang_code = LANGUAGE_DICT.get(tgt_name, 'en')
        gtts_code = GTTS_CODE_MAP.get(lang_code, lang_code)

        if lang_code == 'auto':
            self._set_status("⚠  Select a target language before speaking.", C['status_err'])
            return

        self._set_status("🔊  Generating audio…", C['text_dim'])
        self.root.update_idletasks()

        # Run in thread so UI stays responsive
        def _do_speak():
            tmp = "_tts_voice.mp3"
            try:
                if self._pygame_ok:
                    pygame.mixer.music.stop()

                # Wait a moment then delete old file
                time.sleep(0.05)
                if os.path.exists(tmp):
                    try:
                        os.remove(tmp)
                    except PermissionError:
                        tmp = f"_tts_voice_{int(time.time())}.mp3"

                tts = gTTS(text=text, lang=gtts_code, slow=False)
                tts.save(tmp)

                if self._pygame_ok:
                    pygame.mixer.music.load(tmp)
                    pygame.mixer.music.play()

                self.root.after(0, lambda: self._set_status(
                    "🔊  Playing audio…", C['status_ok']
                ))

            except Exception as e:
                self.root.after(0, lambda: self._set_status(
                    f"✗  TTS failed: {e}", C['status_err']
                ))

        threading.Thread(target=_do_speak, daemon=True).start()

    def _swap_languages(self):
        src = self.source_var.get()
        tgt = self.target_var.get()

        # Don't swap if source is auto
        if src == 'Auto Detect':
            self._set_status("⚠  Select a specific source language to swap.", C['status_err'])
            return

        self.source_var.set(tgt)
        self.target_var.set(src)

        # Also swap text content
        src_text    = self.text_input.get("1.0", tk.END).strip()
        output_text = self._get_output()

        if output_text:
            self.text_input.delete("1.0", tk.END)
            self.text_input.insert(tk.END, output_text)
            self._set_output(src_text)
            self._update_char_count()

        self._set_status(f"↔  Swapped: {tgt}  ⇄  {src}", C['status_ok'])

    def _clear(self):
        self.text_input.delete("1.0", tk.END)
        self._set_output("")
        self.char_var.set("0 / 5000 characters")
        self._set_status("Cleared  •  Ready for new text.")
        self.text_input.focus()


# ─────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app  = TranslatorApp(root)
    root.mainloop()