section .bss
    buf resb 16

section .data
    match db "1337", 10
    match_len equ $ - match

section .text
global _start

_start:
    mov rax, 0
    mov rdi, 0
    mov rsi, buf
    mov rdx, 16
    syscall

    cmp rax, 3
    jne .no_match

    cmp byte [buf], '4'
    jne .no_match
    cmp byte [buf+1], '2'
    jne .no_match
    cmp byte [buf+2], 10
    jne .no_match

    mov rax, 1
    mov rdi, 1
    mov rsi, match
    mov rdx, match_len
    syscall

    xor rdi, rdi
    jmp .exit

.no_match:
    mov rdi, 1

.exit:
    mov rax, 60
    syscall