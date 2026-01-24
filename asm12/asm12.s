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
    jle exit_ok

    mov rbx, r8
    dec rbx
    cmp byte [buf+rbx], 10
    jne rev
    dec r8
    dec rbx

rev:
    xor rcx, rcx

loop:
    cmp rcx, rbx
    jge print
    mov al, [buf+rcx]
    mov dl, [buf+rbx]
    mov [buf+rcx], dl
    mov [buf+rbx], al
    inc rcx
    dec rbx
    jmp loop

print:
    mov rax, 1
    mov rdi, 1
    mov rsi, buf
    mov rdx, r8
    syscall

exit_ok:
    mov rax, 60
    xor rdi, rdi
    syscall

section .bss
buf resb 256
