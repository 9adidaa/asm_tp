global _start

section .text
_start:
    mov rax, 0
    mov rdi, 0
    mov rsi, buf
    mov rdx, 256
    syscall

    xor rcx, rcx
    xor r8, r8

.loop:
    mov al, [buf+rcx]
    cmp al, 0
    je .done
    cmp al, 10
    je .done

    cmp al, 'A'
    jb .chk_lower
    cmp al, 'Z'
    ja .chk_lower
    add al, 32

.chk_lower:
    cmp al, 'a'
    je .vowel
    cmp al, 'e'
    je .vowel
    cmp al, 'i'
    je .vowel
    cmp al, 'o'
    je .vowel
    cmp al, 'u'
    je .vowel
    jmp .next

.vowel:
    inc r8

.next:
    inc rcx
    jmp .loop

.done:
    mov rdi, r8
    call print_int

    mov rax, 60
    xor rdi, rdi
    syscall

print_int:
    mov rax, rdi
    lea rsi, [outbuf+31]
    mov byte [rsi], 10
    mov rbx, 10
    mov rcx, 1

    cmp rax, 0
    jne .conv
    dec rsi
    mov byte [rsi], '0'
    inc rcx
    jmp .write

.conv:
    xor rdx, rdx
    div rbx
    add dl, '0'
    dec rsi
    mov [rsi], dl
    inc rcx
    test rax, rax
    jne .conv

.write:
    mov rax, 1
    mov rdi, 1
    mov rdx, rcx
    syscall
    ret

section .bss
buf    resb 256
outbuf resb 32
