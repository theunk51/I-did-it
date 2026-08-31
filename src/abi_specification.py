import platform
from abc import ABC, abstractmethod
from typing import List

class _ABISpecification(ABC):
    @property
    @abstractmethod
    def os_name(self) -> str: pass

    @property
    @abstractmethod
    def architecture(self) -> str: pass

    @property
    @abstractmethod
    def all_registers(self) -> List[str]: pass

    @property
    @abstractmethod
    def allocatable_registers(self) -> List[str]: pass

    @property
    @abstractmethod
    def caller_saved_regs(self) -> List[str]: pass

    @property
    @abstractmethod
    def callee_saved_regs(self) -> List[str]: pass

    @property
    @abstractmethod
    def argument_regs(self) -> List[str]: pass

    @property
    @abstractmethod
    def return_reg(self) -> str: pass

    # ABI Quirks
    @property
    def shadow_space_size(self) -> int: 
        """Returns shadow space size in bytes (e.g., 32 for Windows x64, 0 for Linux SysV)."""
        return 0

    @property
    def stack_alignment(self) -> int: 
        """Required stack alignment boundary in bytes (usually 16)."""
        return 16

    @property
    def compiler_scratch_regs(self) -> List[str]: 
        """
        Registers reserved by the compiler for expression evaluation and memory moves.
        Never given to the Register Allocator.
        """
        return ["%rax", "%rdx", "%r15"]

    @property
    def pushable_callee_saved_regs(self) -> List[str]:
        """
        Returns all callee-saved registers EXCLUDING the stack frame 
        registers (%rbp, %rsp) so the CodeGenerator can blindly loop over them.
        """
        return [reg for reg in self.callee_saved_regs if reg not in ('%rbp', '%rsp')]

class SystemV_x86_64(_ABISpecification):
    """ABI specification for Linux and macOS on x86_64 hardware (AT&T syntax)."""
    os_name = "Linux/macOS"
    architecture = "x86_64"
    
    all_registers = ["%rax", "%rbx", "%rcx", "%rdx", "%rsi", "%rdi", "%rbp", "%rsp", 
                     "%r8", "%r9", "%r10", "%r11", "%r12", "%r13", "%r14", "%r15"]
    
    allocatable_registers = ["%rbx", "%rcx", "%rsi", "%rdi", 
                             "%r8", "%r9", "%r10", "%r11", "%r12", "%r13", "%r14"]
    caller_saved_regs = ["%rax", "%rcx", "%rdx", "%rsi", "%rdi", "%r8", "%r9", "%r10", "%r11"]
    callee_saved_regs = ["%rbx", "%rsp", "%rbp", "%r12", "%r13", "%r14", "%r15"]
    argument_regs = ["%rdi", "%rsi", "%rdx", "%rcx", "%r8", "%r9"]
    
    # Linux Temp/Scratch: %r10 and %r11 are the cleanest pure-scratch choices.
    # %rax (return value), %rdx (mul/div auxiliary), and arguments are caller-saved 
    # but have secondary structural restrictions.
    return_reg = "%rax"
    shadow_space_size = 0

class Windows_x86_64(_ABISpecification):
    """ABI specification for Windows on x86_64 hardware (AT&T syntax)."""
    os_name = "Windows"
    architecture = "x86_64"

    all_registers = SystemV_x86_64.all_registers
    allocatable_registers = SystemV_x86_64.allocatable_registers
    
    caller_saved_regs = ["%rax", "%rcx", "%rdx", "%r8", "%r9", "%r10", "%r11"]
    callee_saved_regs = ["%rbp", "%rbx", "%rsp", "%rsi", "%rdi", "%r12", "%r13", "%r14", "%r15"]
    
    argument_regs = ["%rcx", "%rdx", "%r8", "%r9"]
    return_reg = "%rax"
    shadow_space_size = 32  # Windows requires 32 bytes of "home space" on the stack




if platform.system() == "Windows":
    ABISpecification = Windows_x86_64()
else:
    ABISpecification = SystemV_x86_64()