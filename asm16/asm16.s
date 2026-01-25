section .data
    search      db  0x31, 0x33, 0x33, 0x37, 0x0A   
    search_len  equ $ - search
    replace     db  0x48, 0x34, 0x43, 0x4B        
    err_msg     db  "Error", 10
    err_len     equ $ - err_msg

section .bss
    fd          resq 1
    file_size   resq 1
    mapped_addr resq 1

section .text
global _start

_start:
   
    pop rcx                
    cmp rcx, 2
    jl  error_exit
    
    pop rdi                 
    pop rdi                 
    mov rax, 2              
    mov rsi, 2              
    mov rdx, 0
    syscall
    cmp rax, 0
    jl  error_exit
    mov [fd], rax

    mov rax, 5              
    mov rdi, [fd]
    sub rsp, 144            
    mov rsi, rsp
    syscall
    cmp rax, 0
    jl  error_exit_cleanup
    
    mov rax, [rsp + 48]     
    mov [file_size], rax
    add rsp, 144            
    cmp qword [file_size], search_len
    jl  error_exit_cleanup

    
    mov rax, 9              
    xor rdi, rdi            
    mov rsi, [file_size]    
    mov rdx, 3             
    mov r10, 1             
    mov r8, [fd]            
    xor r9, r9              
    syscall
    cmp rax, -1
    je  error_exit_cleanup
    mov [mapped_addr], rax

    
    mov rdi, rax            
    mov rcx, [file_size]
    sub rcx, search_len
    jl  unmap_file          

search_loop:
    push rdi
    mov rsi, search
    mov rcx, search_len
    repe cmpsb
    pop rdi
    je  found_pattern
    
    inc rdi
    dec qword [file_size]
    cmp qword [file_size], search_len
    jge search_loop

   
    jmp unmap_file

found_pattern:
    
    mov rsi, replace
    mov rcx, 4              
    rep movsb

unmap_file:
    
    mov rax, 11             
    mov rdi, [mapped_addr]
    mov rsi, [file_size]
    syscall

close_file:
    
    mov rax, 3              
    mov rdi, [fd]
    syscall

    
    mov rax, 60
    xor rdi, rdi
    syscall

error_exit_cleanup:
    
    mov rax, 3
    mov rdi, [fd]
    syscall

error_exit:
    
    mov rax, 1
    mov rdi, 1
    mov rsi, err_msg
    mov rdx, err_len
    syscall
    
    
    mov rax, 60
    mov rdi, 1
    syscall