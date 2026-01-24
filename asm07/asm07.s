global _start

section .text
_start:
    mov rax, 0
    mov rdi, 0
    mov rsi, buf
    mov rdx, 64
    syscall

    mov rdi, buf
    call atoi
    mov rbx, rax

    cmp rbx, 2
    jl not_prime
    cmp rbx, 2
    je prime
    test rbx, 1
    jz not_prime

    mov rcx, 3
check_loop:
    mov rax, rcx
    imul rax, rcx
    cmp rax, rbx
    jg prime

    mov rax, rbx
    xor rdx, rdx
    div rcx
    test rdx, rdx
    jz not_prime

    add rcx, 2
    jmp check_loop

prime:
    mov rax, 60
    xor rdi, rdi
    syscall

not_prime:
    mov rax, 60
    mov rdi, 1
    syscall

atoi:
    xor rax, rax
    xor rcx, rcx
.skip:
    mov bl, [rdi+rcx]
    cmp bl, ' '
    je .inc
    cmp bl, 10
    je .inc
    cmp bl, 13
    je .inc
    cmp bl, 9
    je .inc
    jmp .parse
.inc:
    inc rcx
    jmp .skip

.parse:
    mov bl, [rdi+rcx]
    cmp bl, '0'
    jb .done
    cmp bl, '9'
    ja .done
    sub bl, '0'
    imul rax, rax, 10
    add rax, rbx
    inc rcx
    jmp .parse

.done:
    ret

section .bss
buf resb 64
