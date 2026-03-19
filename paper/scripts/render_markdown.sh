#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p out

TITLE="$(sed -n 's/^\\title{\(.*\)}/\1/p' main.tex | head -n 1)"
AUTHOR="$(sed -n 's/^\\author{\(.*\)}/\1/p' main.tex | head -n 1)"

TMP_BODY="$(mktemp)"
trap 'rm -f "$TMP_BODY"' EXIT

awk '/\\begin\{document\}/{in_doc=1; next} /\\end\{document\}/{in_doc=0} in_doc' main.tex > "$TMP_BODY"

{
  if [ -n "$TITLE" ]; then
    echo "# $TITLE"
    echo
  fi
  if [ -n "$AUTHOR" ]; then
    echo "_Author: $AUTHOR_"
    echo
  fi

  perl -0777 -pe '
    s/\r//g;
    s/^\s*%.*\n//mg;
    s/\\maketitle\s*//g;
    s/\\tableofcontents\s*//g;
    s/\\section\{([^}]*)\}/\n## $1\n/g;
    s/\\subsection\{([^}]*)\}/\n### $1\n/g;
    s/\\subsubsection\{([^}]*)\}/\n#### $1\n/g;
    s/\\paragraph\{([^}]*)\}/\n#### $1\n/g;
    s/\\texttt\{([^}]*)\}/`$1`/g;
    s/\\emph\{([^}]*)\}/*$1*/g;
    s/\\url\{([^}]*)\}/$1/g;
    s/\\cite[t|p]?\{[^}]*\}//g;
    s/\\label\{[^}]*\}//g;
    s/\\ref\{([^}]*)\}/$1/g;
    s/\\begin\{itemize\}\s*//g;
    s/\\end\{itemize\}\s*//g;
    s/\\begin\{enumerate\}\s*//g;
    s/\\end\{enumerate\}\s*//g;
    s/\\item\s+/\n- /g;
    s/\\begin\{equation\}/\n```math\n/g;
    s/\\end\{equation\}/\n```\n/g;
    s/\\begin\{verbatim\}/\n```\n/g;
    s/\\end\{verbatim\}/\n```\n/g;
    s/\\begin\{[^}]*\}\s*//g;
    s/\\end\{[^}]*\}\s*//g;
    s/\\[a-zA-Z]+\*?(\[[^\]]*\])?\{[^{}]*\}//g;
    s/\\[a-zA-Z]+\*?//g;
    s/[ \t]+$//mg;
    s/\n{3,}/\n\n/g;
  ' "$TMP_BODY"
} > out/main.md

echo "Markdown render complete: $ROOT_DIR/out/main.md"
