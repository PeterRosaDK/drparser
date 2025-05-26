import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton, QFileDialog, QLabel, QCheckBox
)
from PyQt5.QtCore import Qt
from collections import Counter
import pysrt
import numpy as np


# Funktion til at konvertere SubRipTime til sekunder
def subriptime_to_seconds(subrip_time):
    return (
        subrip_time.hours * 3600 +
        subrip_time.minutes * 60 +
        subrip_time.seconds +
        subrip_time.milliseconds / 1000
    )

# Funktion til at fjerne mellemrum før tegnsætning
def attach_punctuation(words):
    result = []
    current_word = ""
    
    for word, attaches_to in words:
        if attaches_to == "previous":
            # Hvis det er tegnsætning, append direkte til det nuværende ord
            if current_word:
                current_word += word
            else:
                # Hvis ingen current_word, append til sidste ord i result
                if result:
                    result[-1] += word
                else:
                    result.append(word)
        else:
            # Hvis vi har et current_word, gem det først
            if current_word:
                result.append(current_word)
            # Start et nyt ord
            current_word = word
    
    # Husk at tilføje det sidste ord hvis der er et
    if current_word:
        result.append(current_word)
        
    return result

# Funktion til at beregne median confidence score
def calculate_confidence_score(json_data):
    confidences = []
    results = json_data.get("results", [])
    
    for item in results:
        if item["type"] == "word":
            confidence = item.get("alternatives", [{}])[0].get("confidence", 1.0)
            confidences.append(confidence)
    
    if confidences:  # Beregn gennemsnit hvis der er værdier
        average_confidence = np.mean(confidences) * 100  # Konverter til procent
    else:
        average_confidence = 100.0  # Hvis alt er 1.0, er fejlen 0%
    
    print("Filtered Confidences:", confidences)  # Debugging
    print("Average Error Confidence (%):", average_confidence)  # Debugging
    return average_confidence

class SubtitleApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JSON til SRT")
        self.setGeometry(100, 100, 800, 600)
        self.setAcceptDrops(True)  # Aktiver drag-and-drop

        # Layouts
        layout = QVBoxLayout()
        
        # AI-Score Label
        self.score_label = QLabel("AI Confidence Score: Ikke beregnet")
        layout.addWidget(self.score_label)
        
        # Input Text Area
        self.json_input = QTextEdit()
        self.json_input.setPlaceholderText("Sæt din JSON-fil ind her")
        layout.addWidget(QLabel("JSON-input:"))
        layout.addWidget(self.json_input)
        
        # Output Text Area
        self.srt_output = QTextEdit()
        self.srt_output.setReadOnly(True)
        layout.addWidget(QLabel("SRT-output:"))
        layout.addWidget(self.srt_output)
        
        # Checkbox for merging subtitles
        self.merge_checkbox = QCheckBox("Slå tekster sammen")
        self.merge_checkbox.setChecked(True)  # Som standard er sammenlægning aktiveret
        layout.addWidget(self.merge_checkbox)
        
        # Buttons
        self.load_button = QPushButton("Hent JSON-talegenkendelse")
        self.load_button.clicked.connect(self.load_json_file)
        layout.addWidget(self.load_button)
        
        self.parse_button = QPushButton("Konverter til undertekster med Confidence Score")
        self.parse_button.clicked.connect(self.parse_json_to_srt)
        layout.addWidget(self.parse_button)

        self.save_button = QPushButton("Gem som SRT-fil")
        self.save_button.clicked.connect(self.save_srt_file)
        layout.addWidget(self.save_button)
        
        self.setLayout(layout)
        self.srt_items = []  # To hold SRT data

    def load_json_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json)")
        if file_name:
            with open(file_name, 'r', encoding='utf-8') as file:
                json_data = file.read()
                self.json_input.setText(json_data)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()  # 👑 Dette er det vigtige!
        else:
            event.ignore()


    def dropEvent(self, event):
        print("Drop event modtaget!")  # Debugging

        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            print("Filsti modtaget:", file_path)  # Debugging

            if file_path.endswith(".json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        json_data = file.read()
                        self.json_input.setText(json_data)
                        print("JSON indhold sat i tekstfelt!")  # Debugging
                except Exception as e:
                    self.srt_output.setText(f"Fejl ved indlæsning af fil: {e}")
                break

    def parse_json_to_srt(self):
        try:
            json_data = json.loads(self.json_input.toPlainText())
            
            # Beregn Confidence Score
            confidence_score = calculate_confidence_score(json_data)
            
            # Opdater AI-score label
            self.score_label.setText(f"AI Confidence Score: {confidence_score:.2f}%")
            
            self.srt_output.clear()
            self.srt_items = self.generate_srt(json_data, confidence_score)

            if self.merge_checkbox.isChecked():
                self.srt_items = self.merge_srt_items(self.srt_items)

            self.display_srt_output(self.srt_items)

        except Exception as e:
            self.srt_output.setText(f"Error parsing JSON: {e}")

    def display_srt_output(self, srt_items):
        for item in srt_items:
            start_seconds = subriptime_to_seconds(item.start)
            end_seconds = subriptime_to_seconds(item.end)
            duration = end_seconds - start_seconds  # Beregn varigheden i sekunder
            self.srt_output.append(f"{item.index}\n{item.start} --> {item.end} ({duration:.2f}s)\n{item.text}\n")

    def generate_srt(self, json_data, confidence_score):
        results = json_data.get("results", [])
        srt_items = []

        # Tilføj nultekst med Confidence Score
        job_data = json_data.get("job", {})
        metadata = json_data.get("metadata", {})
        language_info = metadata.get("language_identification", {})
        transcription_config = metadata.get("transcription_config", {})

        null_text = [
            f"Fil: {job_data.get('data_name', 'Unknown')}",
            f"Sprog: {language_info.get('predicted_language', 'Unknown')}",
            f"Konfiguration: {transcription_config.get('operating_point', 'Unknown')}",
            f"Confidence Score: {confidence_score:.3f}"  # Tilføj confidence score her
        ]
        srt_items.append(
            pysrt.SubRipItem(
                index=1,
                start=pysrt.SubRipTime(0, 0, 0, 0),
                end=pysrt.SubRipTime(0, 0, 0, 320),  # 8 frames ved 25 FPS
                text="\n".join(null_text)
            )
        )

        # Tekstblokke fra JSON
        current_block = []
        block_start_time = None
        speaker_counts = Counter()

        index = 2  # Starter fra 2, da nulteksten er blok 1
        for item in results:
            if item["type"] == "word":
                word_data = item.get("alternatives", [{}])[0]
                word = word_data.get("content", "")
                attaches_to = item.get("attaches_to", None)

                speaker = word_data.get("speaker", "Unknown")
                current_block.append((word, attaches_to))
                speaker_counts[speaker] += 1

                if block_start_time is None:
                    block_start_time = item.get("start_time", 0)

            elif item["type"] == "punctuation":
                if current_block:
                    # Tilføj tegnsætningen som et separat element med attaches_to="previous"
                    current_block.append((item["alternatives"][0]["content"], "previous"))
                else:
                    # Hvis blokken er tom, tilføj kun tegnsætningen
                    current_block.append((item["alternatives"][0]["content"], None))

            if item.get("is_eos"):
                dominant_speaker = speaker_counts.most_common(1)[0][0] if speaker_counts else "Unknown"
                block_text = " ".join(attach_punctuation(current_block))
                
                # Gem speaker som metadata på srt_item objektet i stedet for i teksten
                srt_item = pysrt.SubRipItem(
                    index=index,
                    start=pysrt.SubRipTime.from_ordinal(int(block_start_time * 1000)),
                    end=pysrt.SubRipTime.from_ordinal(int(item.get("end_time", 0) * 1000)),
                    text=block_text
                )
                # Tilføj speaker som et attribut på objektet
                srt_item.speaker = dominant_speaker
                
                srt_items.append(srt_item)
                index += 1
                current_block = []
                block_start_time = None
                speaker_counts.clear()

        return srt_items

    def merge_srt_items(self, srt_items):
        merged_items = []
        for i, item in enumerate(srt_items):
            if i == 0:  # Behold nulteksten som den er
                merged_items.append(item)
                continue

            prev_item = merged_items[-1]
            
            # Brug speaker metadata i stedet for at parse teksten
            same_speaker = hasattr(item, 'speaker') and hasattr(prev_item, 'speaker') and item.speaker == prev_item.speaker
            combined_duration = subriptime_to_seconds(item.end) - subriptime_to_seconds(prev_item.start)

            if same_speaker and combined_duration <= 7:
                # Sammensæt teksterne
                prev_item.text = f"{prev_item.text} {item.text}"
                prev_item.end = item.end
            else:
                merged_items.append(item)

        # Renummerer alle undertekster før vi returnerer
        for i, item in enumerate(merged_items, 1):
            item.index = i
        return merged_items

    def save_srt_file(self):
        if not self.srt_items:
            self.srt_output.append("\nNo SRT data to save.")
            return
        
        file_name, _ = QFileDialog.getSaveFileName(self, "Save SRT File", "", "SRT Files (*.srt)")
        if file_name:
            subs = pysrt.SubRipFile(self.srt_items)
            subs.save(file_name, encoding='utf-8')
            self.srt_output.append(f"\nSRT file saved to {file_name}")


if __name__ == "__main__":
    app = QApplication([])
    window = SubtitleApp()
    window.show()
    app.exec_()
