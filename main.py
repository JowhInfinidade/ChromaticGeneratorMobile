#This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

#This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

#You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

import parselmouth
import os
from os.path import exists
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner

class GeneratorGUI(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')

        # File Chooser
        self.filechooser = FileChooserListView(path=os.getcwd())
        layout.add_widget(self.filechooser)

        # Gap Input
        self.gap_input = TextInput(hint_text='Gap', input_filter='float')
        layout.add_widget(self.gap_input)

        # Range Input
        self.range_input = TextInput(hint_text='Semitones', input_filter='int')
        layout.add_widget(self.range_input)

        # Start Note Choice
        self.start_note_choice = Spinner(text='C', values=('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'))
        layout.add_widget(self.start_note_choice)

        # Start Octave Choice
        self.start_octave_choice = Spinner(text='4', values=('1', '2', '3', '4', '5', '6', '7', '8'))
        layout.add_widget(self.start_octave_choice)

        # Pitched Check
        self.pitched_check = CheckBox(active=True)
        layout.add_widget(self.pitched_check)

        # Samples Check
        self.samples_check = CheckBox(active=True)
        layout.add_widget(self.samples_check)

        # Generate Button
        self.generate_button = Button(text='Generate Chromatic', on_press=self.generate_chromatic)
        layout.add_widget(self.generate_button)

        return layout

    def generate_chromatic(self, instance):
        sample_path = self.filechooser.path
        sample_gap = parselmouth.praat.call("Create Sound from formula", "Gap", 1, 0, float(self.gap_input.text), 48000, "0")
        file_index = 0

        while exists(sample_path + os.sep + str(file_index + 1) + ".wav"):
            file_index += 1

        semitones = int(self.range_input.text)
        pitched_sounds = []
        spaced_pitched_sounds = []

        for i in range(semitones):
            starting_key = self.start_note_choice.values.index(self.start_note_choice.text) + 12 * int(self.start_octave_choice.text)

            current_sound = parselmouth.praat.call(parselmouth.praat.call(parselmouth.Sound(sample_path + os.sep + str(i % (file_index) + 1) + ".wav"), "Resample", 48000, 1), "Convert to mono")

            if self.pitched_check.active:
                manipulation = parselmouth.praat.call(current_sound, "To Manipulation", 0.05, 60, 600)
                pitch_tier = parselmouth.praat.call(manipulation, "Extract pitch tier")

                parselmouth.praat.call(pitch_tier, "Formula", f"32.703 * (2 ^ ({i + starting_key + 12}/12))")
                parselmouth.praat.call([pitch_tier, manipulation], "Replace pitch tier")

                pitched_sounds.append(parselmouth.praat.call(manipulation, "Get resynthesis (overlap-add)"))
                spaced_pitched_sounds.append(parselmouth.praat.call(manipulation, "Get resynthesis (overlap-add)"))
            else:
                pitched_sounds.append(current_sound)
                spaced_pitched_sounds.append(current_sound)

            spaced_pitched_sounds.append(sample_gap)

        chromatic = parselmouth.Sound.concatenate(spaced_pitched_sounds)
        chromatic.save(sample_path + os.sep + "chromatic.wav", "WAV")

        if self.samples_check.active and self.pitched_check.active:
            if not os.path.exists(sample_path + os.sep + "pitched_samples"):
                os.makedirs(sample_path + os.sep + "pitched_samples")
            for pitched_sound in pitched_sounds:
                pitched_sound.save(sample_path + os.sep + "pitched_samples" + os.sep + ""f"pitched_{1 + pitched_sounds.index(pitched_sound)}.wav", "WAV")

if __name__ == '__main__':
    GeneratorGUI().run()
