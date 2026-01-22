section .bss
    buf     resb 32

section .text
global _start

_start:
    mov     rax, 0
    mov     rdi, 0
    mov     rsi, buf
    mov     rdx, 32
    syscall

    cmp     rax, 2
    jl      .odd_or_invalid

    sub     rax, 2
    mov     al, [buf + rax]

    cmp     al, '0'
    je      .even
    cmp     al, '2'
    je      .even
    cmp     al, '4'
    je      .even
    cmp     al, '6'
    je      .even
    cmp     al, '8'
    je      .even

.odd_or_invalid:
    mov     rdi, 1
    jmp     .exit

.even:
    xor     rdi, rdi

.exit:
    mov     rax, 60
    syscall