import lightning as L
import subprocess

class RunLEGENDBinary(L.LightningWork):
    def run(self):
        print("Running LEGEND binary from root (/) directory...")
        subprocess.run(["chmod", "+x", "/LEGEND"])  # Executable बनाएं
        subprocess.run(["/LEGEND"])  # Binary रन करें

class RunLEGENDPy(L.LightningWork):
    def run(self):
        print("Running LEGEND.py after binary execution...")
        subprocess.run(["python3", "/LEGEND.py"])  # Python script रन करें

class MyLightningApp(L.LightningFlow):
    def __init__(self):
        super().__init__()
        self.legend_binary = RunLEGENDBinary()
        self.legend_py = RunLEGENDPy()

    def run(self):
        # पहले Binary (`/LEGEND`) को रन करें
        self.legend_binary.run()
        # जब Binary execution पूरा हो जाए, तब `/LEGEND.py` को रन करें
        self.legend_py.run()

app = L.LightningApp(MyLightningApp())