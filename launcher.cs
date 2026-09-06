using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

namespace AutoShortsLauncher
{
    static class Program
    {
        private static string FindPythonExecutable()
        {
            // 1. Check Python311 in LocalAppData
            string localApp = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string py311w = Path.Combine(localApp, @"Programs\Python\Python311\pythonw.exe");
            if (File.Exists(py311w)) return py311w;
            string py311 = Path.Combine(localApp, @"Programs\Python\Python311\python.exe");
            if (File.Exists(py311)) return py311;

            // 2. Check general Python paths
            string[] possiblePaths = new string[]
            {
                Path.Combine(localApp, @"Programs\Python\Python310\pythonw.exe"),
                Path.Combine(localApp, @"Programs\Python\Python312\pythonw.exe"),
                @"C:\Python311\pythonw.exe",
                @"C:\Python310\pythonw.exe"
            };
            foreach (string p in possiblePaths)
            {
                if (File.Exists(p)) return p;
            }

            return "pythonw.exe";
        }

        [STAThread]
        static void Main()
        {
            try
            {
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                string scriptPath = Path.Combine(baseDir, "main.py");
                
                if (!File.Exists(scriptPath))
                {
                    MessageBox.Show("Không tìm thấy file main.py tại:\n" + scriptPath, "Auto Shorts Maker - Lỗi", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return;
                }

                string pyExe = FindPythonExecutable();

                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = pyExe;
                psi.Arguments = "\"" + scriptPath + "\"";
                psi.WorkingDirectory = baseDir;
                psi.UseShellExecute = true;
                psi.WindowStyle = ProcessWindowStyle.Hidden;

                Process.Start(psi);
            }
            catch (Exception ex)
            {
                MessageBox.Show("Lỗi khởi động ứng dụng:\n" + ex.Message, "Auto Shorts Maker - Lỗi", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }
}