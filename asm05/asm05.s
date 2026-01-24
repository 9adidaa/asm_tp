global _start

section .text
_start:
    mov rax, [rsp]
    cmp rax, 2
    jl  exit_ok

    mov rsi, [rsp+16]

    xor rdx, rdx
len_loop:
    cmp byte [rsi+rdx], 0
    je  print
    inc rdx
    jmp len_loop

print:
    mov rax, 1
    mov rdi, 1
    syscall

    mov rax, 1
    mov rdi, 1
    mov rsi, nl
    mov rdx, 1
    syscall

exit_ok:
    mov rax, 60
    xor rdi, rdi
    syscall

section .data
nl db 10
