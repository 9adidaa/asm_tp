global _start

section .text
_start:
    mov rax, [rsp]
    cmp rax, 2
    jl not_elf

    mov rdi, [rsp+16]

    mov rax, 2
    xor rsi, rsi
    xor rdx, rdx
    syscall
    cmp rax, 0
    jl not_elf
    mov r12, rax

    mov rax, 0
    mov rdi, r12
    mov rsi, hdr
    mov rdx, 5
    syscall

    mov rax, 3
    mov rdi, r12
    syscall

    cmp byte [hdr], 0x7F
    jne not_elf
    cmp byte [hdr+1], 'E'
    jne not_elf
    cmp byte [hdr+2], 'L'
    jne not_elf
    cmp byte [hdr+3], 'F'
    jne not_elf

    cmp byte [hdr+4], 2
    jne not_elf

    mov rax, 60
    xor rdi, rdi
    syscall

not_elf:
    mov rax, 60
    mov rdi, 1
    syscall

section .bss
hdr resb 8
