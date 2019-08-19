python 是一门极简的语言，语言简洁学习起来也是相当轻松的，但是依然有一些高级技巧，例如装饰器，协程，并发会让人感觉困惑，失望与沮丧，本文将重点讲解 python装饰器的使用，使用常用的例子让我们更直观的看到装饰器的强大表达能力，最后也给出了编写装饰器常见的工具。
    
   熟悉 java的同学一定熟悉注解的使用，借助于注解可以定义元数据配置，我们常常有这种感受，"只要加上这个注解，我的组件就会被注册进去"，"只要加上这个注解，就会添加事务控制"，也会困惑，"为什么加了这个注解依然没有生效?"， python 没有提供像Java似的注解，但是提供了相比注解表达能力更加强大的装饰器。
   例如 web框架 Flask 中的route ，errorhandler，及 python 自带的 property，staticmethod等。 实际上java 注解能实现的功能，python 的装饰器绝大部分都是可以胜任的，装饰器更像 Java 中注解加上Aop两者的组合， 这个结论最后我们会重点讨论，先按下不表。现在首先以日志打印的简单例子初步讲解一下装饰器的使用
###  1.0  装饰器的简单例子
```
def log(func):                                      #@1
    def func_dec(*args, **kwargs):                  #@2
        r = func(*args, **kwargs)                   #@3
        print("didiyun execute done:%s" % func.__name__)
        return r

    return func_dec

@log                                                #@4
def test_dec(size, length, ky=None):
    print "didiyun execute test_dec param:%s, %s, %s" % (size, length, ky)


def test():
    test_dec(ky="yuhaiqiang", length=3, size=1)

""
输出结果可以看到装饰器的装饰逻辑已正确被执行
didiyun execute test_dec param:1, 3, yuhaiqiang
didiyun execute done:test_dec
""

@1 定义 log 装饰器，输入参数func是需要被装饰的函数，本例中输出打印是 test_dec
@2 定义一个装饰函数，参数类型包括变长的位置参数和名字参数，适应被装饰函数不同的参数组合，这种写法可以代表任意参数组合 
@3 执行实际的函数func_dec， 注意处理返回值，不要"吞掉"被装饰函数的返回值
@4 在被装饰函数上添加装饰器，注意此处不要加()，后面会解释具体原因，了解该原因，就能完全了解装饰器的小九九
```
装饰器可以在函数外层添加额外的功能装饰原函数， 本例的装饰器只是在函数外层打印一行日志，实现的是非常简单的功能，实际中装饰器并不是"仅仅打印日志的雕虫小技"，还能实现其他更有用的功能

### 2.使用装饰器巧用文件锁
#### 2.1 使用 fcntl 实现文件锁

```
class Lock:
    def __init__(self, filename, block=True):
    #block 参数为 true代表阻塞式获取。  False为非阻塞，如果获取不到立刻返回 false
        self.filename = filename
        self.block = block
        self.handle = open(filename, 'w')

    def acquire(self):
        if not self.block:
            try:
                fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except:
                return False
        else:
            fcntl.flock(self.handle, fcntl.LOCK_EX)
            return True
    def release(self):
        fcntl.flock(self.handle, fcntl.LOCK_UN)
        self.handle.close()
```
借助于 fcntl 库 我们已经实现文件锁，感兴趣的读者可以深入了解一下 fcntl 库，下面我们以文件锁为例，介绍一下装饰器很实用很常见的一些功能。

#### 2.2  定义文件锁装饰器
```
def file_lock(lock_name, block=True):                               #@1 
    def wrapper(func):
        def f(*args, **kwargs):
            name = lock_name
            lock = Lock(name, block)
            acquire = lock.acquire()
            if not acquire:
                print("failed to acquire lock:%s,now ignore" % name)
                return                                              #@2
            print("acquire process lock:%s" % name)
            try:
                return func(*args, **kwargs)
            finally:
                lock.release()                                      #@3
                print("release process lock:%s" % name)
        return f
    return wrapper
    
@file_lock(name="/var/local/file", block=True)                      #@4
def get_length():
    pass
get_length()

输出                                                                 #@5
acquire process lock:/var/local/file
execute test_dec param:1
release process lock:/var/local/file
```
1. 定义 file_lock 装饰器，接受两个参数， lock_name:锁路径， block: 是否阻塞式的获取
2. 该处在获取锁失败时，仅仅返回了 None， 调用方无法 明确知道None 是 get_length 的返回值还是获取锁失败，实际上应该抛出一个异常，交给
上游调用方去处理 获取锁操作失败的异常
3. try finally 保证锁一定可以被释放
4. 在使用文件锁的时候，还需要提供锁的值，能否提供默认值呢?只对该实例方法加锁，读者可以考虑一下如何实现。此外细心地读者能比较出来，file_lock装饰器，添加了括号()，但是两者的区别可不仅仅因为一个有参数，一个无参，后一节解释下装饰器的语法糖本质
5. 实际在项目中使用时，经常会遇到文件锁的问题， 在项目调试阶段， 由于经常需要手动终止强杀程序， 这样会导致文件锁没有被正确清理，读者可以考虑
将文件锁指定在一个固定的目录， 每次进程启动时，检测是否有同路径进程，如果没有， 可以清理该目录，如果存在同路径进程，说明现在有并发执行，不清理该目录。 如果没有清理功能可能会导致永远无法获取到锁。 如果不实际使用以上代码实现文件锁，可以
忽略该问题，不影响理解装饰器。 感兴趣的读者可以试试，希望能提出更好的文件锁方案


使用文件锁之后，调用该方法必须先获取到锁，否则只能先阻塞。  因此实际的处理方法不需要处理同步逻辑， 只需要一行装饰器， 就额外扩展了同步功能， 通过异常控制，还能保证文件锁一定可以被释放， 避免文件锁泄露， 通过装饰器我们还可以实现很多其他有用的功能
，但是文件锁装饰器的实现已经相比日志装饰器复杂了， 仔细观察， 它已经 嵌套了 三层函数，后续我们会优化这个问题。


#### 2.3 解释1.0 的疑问，何时使用装饰器需要添加 括号()
  在1.0 日志装饰器的例子我们留下了一个疑问，为什么 log 装饰器不需要加() ，而文件锁装饰器的使用却加了()
 
   回到1.0 的装饰器实现，假如我们不使用@ log 的方式，使用如下方式呢?能不能实现相同的逻辑?
  ``` 
   @log
   def foo():
       pass
   
   foo() # 相当于 log(foo)()，log(func) 返回装饰函数，最后的括号代表执行
   
   foo = log(foo) # 就是装饰器语法糖帮我们做的
  ```
  log 方法接受的参数是 func ， 自然当手动显式 调用 log 装饰 foo 函数时， 丝毫不影响实现装饰的功能. 但是显得我们很啰嗦很蠢，  幸福的是 python 
  提供了装饰器的语法糖， 使用该语法糖就好像我们手动执行装饰一样。 但是如果我们加上括号代表什么意思呢? @log() 的写法， 不就相当于调用了 log 函数，但是又不给其传参?
  实际 python 解释器也是这么"抗议" 我们的。
  
  但是为什么文件锁又加上了括号呢?答案是，装饰器有时候需要一些额外的参数，例如 Flask 中我们常用的 route，我们需要告诉 Flask， 如何 将url映射到具体的 handler， 自然需要告诉 route， 需要绑定的 url 是什么， 和 spring  的@RequestMapping作用类似
  
  当装饰器加上参数之后， 惊讶的发现装饰器更像是三层函数了.....， 可理解性已经极差了， 但是一旦理解之后我们会发现三层函数是原因的
   
  不妨这样理解， 当装饰器没有参数， 就像log 装饰器，该装饰器接受参数为 func， 我们称其为"两层"装饰器 ，以上我们已经分析了它的的原理，
  foo = log(foo). 装饰器的@标记等于告诉 python解释器， "你把@下一行的函数，作为参数传给该装饰器，然后把返回值赋值给该函数"， 相当于执行 foo = log(foo)
  当我们调用 foo() 相当于是调用 log(foo)()。
  
  对于带参数的装饰器file_lock(name，block)， 我们分成两个阶段理解，回顾一下 file_lock 的三层函数实现，我们在第二层定义了一个 wrapper 函数，该函数接受了一个 func 参数,随后我们在 file_lock
  的最后将其return， 我们可以这样认为
   ```
@file_lock(name="/var/local/test",block=True)
def test()
    pass
    
wrapper = file_lock(name, block) #第一阶段
test = wrapper(test)    #第二阶段
   ```
   第一阶段执行了最外层的函数file_lock， 返回了 wrapper。   第二阶段，使用 wrapper 装饰 test， 第二阶段我们已经熟悉理解了。
   实际上， 只是第一阶段是多执行的。  由于我们多给它加了一个括号， python 解释器自然会去执行该函数， 该函数返回另一个装饰函数， 这样就到了第二阶段。 
   
  python 解释器希望我们这样去理解，否则三层函数的写法很让人崩溃。后续我们继续探索装饰器，能不能实现相同的功能，但是能摆脱编写三层函数的噩梦。
   
以上分析了带参数和不带参数的装饰器的区别，及如何在心里去理解与接受这种写法， python 通过语法糖， 函数之上的装饰器定义 代替蠢笨的手动装饰调用。 我们可以实现复杂的装饰器 但却能提供极其
优雅的使用方式给调用方， 还是 让人鼓舞的，事实上， python的框架中大量的使用了装饰器。也说明了装饰器的强大与优雅。


### 3.python 装饰器方法的执行时机与顺序
python 是解释执行的语言，我们做一个小实验，以上例子先定义 log 装饰器，而后再使用 log装饰器，如果置换一下顺序
```
@log("say some thing")
def test_dec(size， length, ky=None):
    print "execute test_dec param:%s, %s, %s" % (size, length, ky)

def log(info=None):
    def wrapper(func):
        def func_dec(*args, **kwargs):
            r = func(*args, **kwargs) 
            print("execute done:%s" % func.__name__)
            return r
        return func_dec
    return wrapper
```
毫无疑问，这样会报语法错误， python是 从python文件从上到下执行解释执行， 只有已经定义log， 才能使用它。
 在python 中，函数是一等公民， 函数也是对象，在定义函数时，也就是在声明一个函数对象
```
def foo():
    pass
```
def foo()就是在声明一个函数对象， foo 即是该函数对象的引用， 我们可以额外定义该对象的属性， 通过dir(foo) 查看一下该函数对象有哪些属性，其实是和类实例对象没有区别的

以上提过 test 被 log装饰 后， test() 等同于log(test)() ， python 装饰器解释执行完 @log def test()，等同于test=log(test)  此时 test引用的函数对象是 log装饰后的函数对象
```
@log
def test():
    pass
test=log(test)
``` 
#### 3.2 装饰器的执行顺序
实际开发中我们经常会遇到使用多个装饰器，如果读者理解了3.0，及以上的函数对象的概念，其实应能能猜出来装饰器的装饰顺序，自然是从上往下执行的
foo = a(b(c(foo))) 但是实际的代码执行顺序是 c->b->a 
```
@a
@b
@c
def foo()
    pass
```
以上我们使用日志装饰器和文件锁装饰器介绍了装饰器的使用，并且讨论了带参数及不带参数装饰器的区别。其中"三层函数"的定义方式可读性非常差，在下一节将重点讨论如何使用类实现装饰器，简化三层装饰器的逻辑，减少相似代码的编写
### 4. 装饰器类的设计
在本节中，我们重点优化三层装饰器的编写，除此之外，笔者在实际开发中还发现了其他常见的需求，
例如
1. 暂存装饰器的参数。  期望通过被装饰函数找到装饰器参数， 笔者在自动化测试中就使用装饰器定义测试 case， 需要在 case 中配置元数据信息，在实际的执行引擎部分，访问该元数据信息。就是将元数据信息放到函数对象中
2. 注册被装饰函数对象。 例如某些 web 框架，注册 handler，  需要在装饰器中实现某些注册逻辑

从以上三点出发，可以看到装饰器的逻辑有某些通用的部分，然而以上装饰器的例子都是通过函数实现的， 但函数在内部状态， 继承等方面明显不如类，所以我们尝试使用类实现装饰器。并尝试实现一个通用的装饰基类

#### 4.1 思路
python 提供了很多奇异方法，所谓的奇异方法是指，只要你实现了这个方法，就可以使用 python 的某些工具方法，例如实现__ len__ 方法，可以使用 len() 获取长度，实现__ iter__ 可以使用 iter方法返回一个迭代器，其他方法
还有 "\_\_eq\_\_"，"\_\_ne\_\_"， "\_\_next\_\_"， 等。 其中当实现__ call__ 方法时， 类可以被当做一个函数使用，例如以下示例
```
class FuncClass(object):
    def __call__(self):
        print("didiyun")

>>>F = FuncClass()
>>>F()
didiyun
```
是否也可以使用 python 的这个特性实现装饰器呢?答案是可以的，让我们来实现一个装饰基类， 解决以上的痛点
```
class BaseDecorator(object):
    def __call__(self， *_, **kwargs):                           #@1
        return self.do_call(**kwargs)                           #@2

    def do_call(self, *_, **decorator_kwargs):
        def wrapper(func):
            wrapper.__explained = False

            @wraps(func)                                        #@3
            def _wrap(*args, **kwargs):
                if not wrapper.__explained:                     #@4
                    self._add_dict(func, decorator_kwargs)
                    wrapper.__explained = True

                return self.invoke(func, *args, **kwargs)       #@5

            self._add_dict(_wrap, decorator_kwargs)             
            _wrap = self.wrapper(_wrap)                         #@6
            return _wrap

        return wrapper

    def wrapper(self, wrapper):
        return wrapper

    def _add_dict(self, func, decorator_kwargs):
        for k, v in decorator_kwargs.items():
            func.__dict__[k] = v

    def invoke(self, func, *args, **kwargs):
        return func(*args, **kwargs)

BaseDecorator实现的并不是具体的某个装饰器逻辑,它可以作为装饰器类的基类，以上我们曾分析编写装饰器通用的需求已经痛点。以下先具体讲解这个类的实现，而后在讨论如何使用
1. __call__ 函数签名，*_ 代表忽略变长的位置参数，只接受命名参数。实际的装饰器中，一般都是使用命名参数.代码可读性高
2. __call__ 本身的实现逻辑委托给了 do_call 方法，主要是考虑， BaseDecorator 作为装饰基类，需要提供某些工具方法及可扩展方法，但是__ call__ 方法本身无法被继承，所以我们退而求次，将工具方法封装在自定义方法中，子类还是需要重新
实现__ call__， 并调用 do_call 方法， do_call 方法的签名和__ call__ 相同
3. functools提供了 wraps 装饰器， 以上我们分析过python是使用装饰后的函数对象替换之前的函数对象达到装饰的效果， 可能有人会有疑问，如果 之前的函数对象有一些自定义属性呢? 装饰后的新函数会不会丢掉，答案是肯定的， 我们可以访问之前的函数对象，给其设置属性，
 这些属性会被存储在 对象的__ dict__ 字典中， 而wraps 装饰器会把原函数的__ dict__拷贝到新的装饰后的函数对象中， 因此 wraps 装饰后，就不会丢掉原有的属性， 而不使用则一定会丢掉。 感兴趣的读者可以点开 wraps 装饰器，看一下具体实现逻辑
4. 在本节开始，我们提出装饰器的通用需求，其中之一是需要将装饰器的参数存放到被装饰的函数中，_add_dict方法便是将装饰器参数设置到原函数以及装饰后的函数中
5. invoke 负责实现具体的装饰逻辑，例如日志装饰器仅仅是打印日志，那么该方法实现就是打印日志，以及调用原函数。  文件锁装饰器，则需要先获取锁后在执行原函数，具体的装饰逻辑在该方法中实现， 具体的装饰器子类应该重写该方法。下一节我们继承该BaseDecorator重写以上的日志及文件锁装饰器
6. invoke 方法是装饰函数调用时被触发的， 而 wrapper 方法只会被触发一次，当 python 解释器执行到@log时，会执行该装饰器的wrapper 方法。相当于，函数被定义的时候，执行了 wrapper方法，在该方法内可以实现某些注册功能。将函数和某些键值映射起来放到字典中，例如 web 框架的 url和handler映射
关系的注册
```
BaseDecorator 抽出来了 invoke，wrapper 目的是让子类装饰器可以在这两个维度上扩展，分别实现装饰，及某些注册逻辑，在下一节我们尝试重写日志及文件锁装饰器，更直观的感受BaseDeceator 给我们带来的便利
#### 4.2 重写日志及文件锁装饰器
```
class _log(BaseDec):
    def invoke(self, func, *args, **kwargs):    #@1
        print("execute done:%s, %s" % (func.__name__,func.desc) ) #@2
        return func(*args, **kwargs)

    def __call__(self, desc):
        return self.do_call(desc=desc)
log = _log()                                  #@2 

1. invoke方法中包括原函数以及原函数的输入参数，该输入参数不是装饰器的参数信息
2. 通过 func 可以访问到装饰器中定义的 desc 参数信息
3. 创建装饰器实例， 便可以像之前一样使用 @log，需要注意的是，该装饰类变成单例， 在定义装饰逻辑的时候，不要轻易在 self 中储存变量
```
通过重写日志装饰器，  可以看到已经摆脱了三层函数的噩梦， 成功的分离了装饰器的基本代码，以及装饰逻辑代码，我们可以更加聚焦于装饰逻辑的核心代码编写，同时可以通过原函数访问装饰器中输入的参数，例如可以访问到日志装饰器的 desc
以下我们再重写文件锁装饰器
```
class _file_lock(BaseDec):
    def invoke(self， func, *args, **kwargs):
        name = func.name                                        #@1 
        lk = Lock(name, True)
        acquire = lk.acquire()
        if not acquire:
            print("failed to acquire lock:%s,now ignore" % name)
            return

        print("acquire process lock:%s" % name)
        try:
            return func(*args, **kwargs)
        finally:
            lk.release()
            print("release process lock:%s" % name)

    def __call__(self, name, block=True):
        return self.do_call(name=name, block=block)             #@2
        
file_lock = _file_lock()                                        #@3

1. 可以通过 func 访问到装饰器中定义的 name 参数
2. 把参数传给 do_call 委托执行
3. 创建文件锁实例,其他位置就可以使用@file_lock了
```
使用新的装饰基类后， 编写新的装饰器子类，是非常轻松方便的事情， 不需要再蹑手蹑脚的定义复杂的三层函数， 不需要重复的设置装饰器参数， 如果我们在项目中大量使用装饰器， 不妨使用装饰基类， 统一常见的功能需求。装饰器的更多用法还需要读者去发掘，但是熟悉 java 的同学
一定熟悉 aop 的理念， 笔者深受 java 折磨多年， 对 aop也几分偏爱， 在我看来， python 的装饰器是 java 中的注解加 aop 的结合。下一节我们横向对比一下 java 注解与 python 装饰器的相似点， 论证文章开头我们留下的一个论点
### 5.对比 Java 的注解
之所以对比 java 注解，主要是笔者想从 java 的某些用法得到某些借鉴与参考， 以便于我们应用到 python 中，通过两种语言的对比可以让我们更深刻的理解语言设计者添加该特性的初衷，以便更好的使用该特性。 更重要的是，让我们面对不同语言的异同 有更大的包容性， 站在欣赏的角度去对比思考，对于我们快速掌握新的语言十分有益。本节绝不是
为了争吵两种语言的优劣， 更不想挑起语言的战争

装饰器和注解最直观的相似点可能就是@艾特符号了， python 使用相同的符号 对于 java 程序员是一种"关照"。 因为 java 程序员对于注解有一种特殊的迷恋， 第三方框架就是使用眼花缭乱的注解 帮助 java 程序员实现一个个神奇的功能。而装饰器也是可以胜任的

java 的注解本身只是一种元数据配置，在没有注解之前， 如果实现相同的元数据配置只能依赖于 xml 配置， 有了注解之后，我们可以把元数据配置和代码放到一起，这样更加直观， 也更便于修改，至于某些人说 xml配置 可以省却编译打包， 其实在笔者经历的项目中，不论是改代码还是改配置都是需要重新走发布流程， 严禁直接修改配置重启程序(除极特殊情况)。

注解和注解解释器是密不可分的，定义注解之后，首先就应该想到如何定义解释器，读取注解上的元数据配置，使用该元数据配置做什么。
 
 最常见的是使用方式是使用注解注册某些组件，开启某项功能，例如 spring 中使用 Component注册 bean，使用 RequestMapping 注册 web url 映射， junit 使用 Test 注册测试 Case， Spring boot 中使用 EnableXXX 开启某些扩展功能等等，注解解释器首先需要获取到
Class 对象使用反射获取到注解中的元数据配置，然后实现"注册"， "开关"逻辑。 以上在我们实现的解释器基类中，我们也实现了类似的功能，我们把装饰器的参数存放到具体的函数对象中， 实际等同于注解的元数据配置， 读者也可以扩展， 添加一个标记， 标记该函数对象确实被某装饰器装饰过。 这样便能像 java 一样轻松的实现某些注册或者开关功能。
    
 除此之外，注解作为元数据配置，可以作为 aop 的切面，这也是注解被广泛使用的原因， 注解可以配置在类，属性，方法之上， "注册" 功能一般是配置在类上， 如果使用注解切面，需要将注解配置在方法之上。以下列出使用注解 aop 可以实现的功能
        
       1. 异常拦截 在使用该注解的函数切面上，将异常拦截住，可以做一些通用的功能，例如异常上报，异常兜底，异常忽略等
       2. 权限控制， 日志记录。 可以控制注解方法的切面的用户访问权限，也可以记录用户操作
       3. 自动重试， 异步处理。如果我们希望异步调用某方法，或者某些需要异常重试的方法，可以使用注解定义切面， 添加异步或重试处理
  注解，提供了非常灵活的切面定义方式，以上三种只是常见的使用方式，当注解定义了切面， aop 会替换被代理的类， 添加某些代理逻辑， 抛开底层实现原理， 实际上aop这种机制和 python 的装饰器区别并不是很大， 设计模式中装饰器和代理模式本身就非常相似，  以上注解可以实现的功能， python 的装饰器都是可以一一实现的。在函数被定义的时刻装饰器就已经生效了， 而 aop也是通过编译期或者运行期在实际调用之前代理。
  python 的装饰器本身也是一个函数，它通过语法糖的方式，帮我们实现了装饰，而 静态类型的java 选择了动态修改字节码，编译器织入等更加复杂的技术实现了类似的功能。 不同的底层实现， 并不能影响在使用方式及场景上互相借鉴。 所以笔者还是认为
  装饰器更像 java 注解+ aop 的组合。 这样对比 对于java 程序可能更容易理解，更好的使用装饰器。



