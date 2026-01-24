global _start

section .text
_start:
    mov rax, 0
    mov rdi, 0
    mov rsi, buf
    mov rdx, 256
    syscall

    mov r8, rax
    test r8, r8
    jle not_pal

    mov rbx, r8
    dec rbx
    cmp byte [buf+rbx], 10
    jne .len_ok
    dec rbx
    dec r8

.len_ok:
    xor rcx, rcx

check:
    cmp rcx, rbx
    jge pal

    mov al, [buf+rcx]
    mov dl, [buf+rbx]
    cmp al, dl
    jne not_pal

    inc rcx
    dec rbx
    jmp check

pal:
    mov rax, 60
    xor rdi, rdi
    syscall

not_pal:
    mov rax, 60
    mov rdi, 1
    syscall

section .bss
buf resb 256
