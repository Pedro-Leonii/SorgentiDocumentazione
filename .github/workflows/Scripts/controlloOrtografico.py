import subprocess
import os
import re
import shlex
import urllib.parse

pull_req_msg = []

command_aspell_it = [
	"aspell", "list", "--mode=tex", "--lang=it", "--home-dir=.", "--ignore-case", 
	"--encoding=utf-8", "--add-tex-command='label p'", "--add-tex-command='hyperref op'", "--add-tex-command='texttt p'", "--add-tex-command='dirtree p'", 
	"--add-tex-command='href pp'", "--add-tex-command='ref p'"
]

command_aspell_en = [
	"aspell", "list", "--lang=en", "--encoding=utf-8"
]

def sanifica(txt):
	patterns = [
		r'\\begin{lstlisting}.*?\\end{lstlisting}', 
		r'\\lstinline\|.*?\|',
		r'\\lstinline\+.*?\+'
	]

	for p in patterns:
		txt = re.sub(p, '', txt, flags=re.DOTALL)

	return shlex.quote(txt)

def get_lines(e, txt):
	line_n = 1
	err_line_numbers = []
	for line in txt.split('\n'):
		if line.find(e):
			err_line_numbers.append(line_n)
		line_n+=1
	return err_line_numbers

subprocess.check_output('git fetch origin develop', shell=True)
diffs = subprocess.check_output('git diff --merge-base origin/develop --name-only', shell=True).split()
curr_br = subprocess.check_output('git rev-parse --abbrev-ref HEAD', shell=True)

for diff in diffs:  # scorre le diff di git dal HEAD del ramo feature fino al suo commit di origine
	if diff.endswith(b'.tex') and os.path.exists(diff):  # file è un file latex ed è stato modificato
		with open(diff, 'r') as f:  # aperto il file da controllare

			link = f'https://github.com/ALT-F4-eng/SorgentiDocumentazione/blob/{urllib.parse.quote(curr_br, safe='')}{diff}'
			txt = f.read()
			file_sanificato = sanifica(txt)

			# Avvia il processo, passando il contenuto direttamente tramite stdin
			proc_aspell_it = subprocess.Popen(command_aspell_it, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
			# Passa il contenuto del file_sanificato tramite stdin al primo processo
			errori_it, error_proc = proc_aspell_it.communicate(file_sanificato)

			# Seconda esecuzione aspell in inglese
			proc_aspell_en = subprocess.Popen(command_aspell_en, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
			# Passa errori del primo processo al secondo processo tramite stdin
			errori, error_proc = proc_aspell_en.communicate(errori_it)

			errori = list(dict.fromkeys(errori.split('\n')))

			if errori:
				pull_req_msg.append(f'## Il file {diff} contiene i seguenti potenziali errori:')
				for e in errori:
					pull_req_msg.extend([f'- ⚠️ - parola: ***{e}*** - riga: ***{pos}*** - [link alla riga]({link})' for pos in get_lines(e, txt)])

with open('errori.md', 'w') as er_file:
	er_file.write("\n".join(pull_req_msg))


