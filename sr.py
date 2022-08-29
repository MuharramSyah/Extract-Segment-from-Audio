import speech_recognition as sr
import logging
logging.basicConfig(filename='log/logging.txt', filemode='w', format='%(asctime)s - %(name)s [%(levelname)s] - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class Speech:
    def __init__(self, lang="id-ID"):
        self.ear = sr.Recognizer()
        self.lang = lang

    def extract_from_file(self, file):
        with sr.AudioFile(file) as source:
            audio = self.ear.record(source)

        try:
            text = self.ear.recognize_google(audio, language=self.lang)
        except LookupError as e:
            logging.warning("Could not understand audio")
            return "I didn`t get it, please try again"
        except sr.UnknownValueError as e:
            logging.warning("Could not understand audio")
            return "i didn't get it, please try again"
        except sr.RequestError as e:
            logging.error("Could not request results; {0}".format(e))
            return "Could not request results; {0}".format(e)
        else:
            return text

    def text_from_microphone(self, sample_rate=48000, chunk_size=2048):
        with sr.Microphone(sample_rate=sample_rate, chunk_size=chunk_size) as source:
            self.ear.adjust_for_ambient_noise(source)
            audio = self.ear.listen(source)
        try:
            text = self.ear.recognize_google(audio, language=self.lang)
        except LookupError as e:
            logging.warning("Could not understand audio")
            return "I didn`t get it, please try again"
        except sr.UnknownValueError as e:
            logging.warning("Could not understand audio")
            return "i didn't get it, please try again"
        except sr.RequestError as e:
            logging.error("Could not request results; {0}".format(e))
            return "Could not request results; {0}".format(e)
        else:
            return text
