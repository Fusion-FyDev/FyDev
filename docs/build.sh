#!/bin/bash 
pandoc  --write docx  --toc -o _build/UserManual.docx --reference-doc=custom-reference.docx -f markdown  UserManual.md
pp source_code_1.md |pandoc -o _build/source_doc_1.docx
# pp source_code_2.md |pandoc -o ../_build/source_doc_2.docx