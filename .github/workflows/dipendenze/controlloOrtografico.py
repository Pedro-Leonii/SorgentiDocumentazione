import subprocess
import os
import urllib.parse

# Esegue N comandi in pipe ognuno passato come array di stringhe
def exec_commands(*commands):
	res = subprocess.Popen(commands[0], stdout=subprocess.PIPE, text=True)
	for command in commands[1:]:
		res = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=res.stdout, text=True)
	return res.stdout.read().strip()

pull_req_msg = []

dic_path = exec_commands(['find', '.', '-type', 'f', '-name', '*.pws'])

# Comando che esegue il controllo grammaticale usando il dizionario italiano
command_aspell_it = [
	'aspell', '-t', 'list', '--lang=it', '--ignore-case=true', f'--personal={dic_path}', '--add-tex-command=label p', '--add-tex-command=hyperref op', '--add-tex-command=texttt p', '--add-tex-command=dirtree p', '--add-tex-command=href pp', '--add-tex-command=ref p'
]

# Comando che esegue il controllo grammaticale usando il dizionario inglese
command_aspell_en = [
	'aspell', 'list', '--lang=en', '--encoding=utf-8', '--ignore-case=true'
]


exec_commands(['git', 'fetch', 'origin', 'main'])
diffs = exec_commands(['git', 'diff', '--merge-base', 'origin/main', '--name-only']).split('\n')
curr_br = exec_commands(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])

for diff in diffs:  # scorre le diff di git dal HEAD del ramo feature fino al suo commit di origine
	if diff.endswith('.tex') and os.path.exists(diff):  # file è un file latex ed è stato modificato
		with open(diff, 'r') as f:  # aperto il file da controllare

			link = f'https://github.com/ALT-F4-eng/SorgentiDocumentazione/blob/{urllib.parse.quote(curr_br, safe='')}{diff}'

			errors = exec_commands(['cat', diff], command_aspell_it, command_aspell_en)	

			errors = list(dict.fromkeys(errors.split('\n')))
			errors = [e for e in errors if e]

			if errors:
				pull_req_msg.append(f'## Il file {diff} contiene i seguenti potenziali errori:')
				for e in errors:
					lines_n = exec_commands(['cat', diff], ['grep', '-nw', e], ['cut', '-d:', '-f1']).split('\n')
					pull_req_msg.extend([f'- ⚠️ - parola: ***{e}*** - riga: ***{line_n}*** - [link alla riga]({link}#{line_n})' for line_n in lines_n])

with open('errori.md', 'w') as er_file:
	er_file.write("\n".join(pull_req_msg))
