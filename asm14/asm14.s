global _start

section .text
_start:
    mov rax, [rsp]
    cmp rax, 2
    jl exit_ok

    mov rdi, [rsp+16]

    mov rax, 2
    mov rsi, 577
    mov rdx, 420
    syscall

    cmp rax, 0
    jl exit_ok

    mov r12, rax

    mov rax, 1
    mov rdi, r12
    mov rsi, msg
    mov rdx, msglen
    syscall

    mov rax, 3
    mov rdi, r12
    syscall

exit_ok:
    mov rax, 60
    xor rdi, rdi
    syscall

section .data
msg db "Hello Universe!", 10
msglen equ $ - msg
