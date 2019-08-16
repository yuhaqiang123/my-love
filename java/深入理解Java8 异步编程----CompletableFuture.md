
 Java对并发编程提供了众多的工具，本文将重点介绍 Java8中CompletableFuture。  笔者在自己搜索资料及实践之后，避开已经存在的优秀文章写作内容与思路，将以更加浅显的示例与语言，介绍 CompleatableFuture， 同时提供自己的思考。最后本文会附上其他优秀的文章链接供读者更详细学习与理解。

### 1 .理解 Future
当处理一个任务时，总会遇到以下几个阶段
    
    1.提交任务
    2.执行任务
    3.任务完成的后置处理

以下我们简单定义，构造及提交任务的线程为生产者线程， 执行任务的线程为消费者线程， 任务的后置处理线程为后置消费者线程

根据任务的特性，会衍生各种各样的线程模型。其中之一包括 Future 模式。 以下我们先以最简单的例子迅速对 future 有个直观理解，然后再对其展开讨论

    例1.1     
     ExecutorService executor = Executors.newFixedThreadPool(3);
     Future future = executor.submit(new Callable<String>() {
    
         @Override
         public String call() throws Exception {
             //do some thing
             Thread.sleep(100);
             return "i am ok";
         }
     });
     println(future.isDone());
     println(future.get());
  

在本例中首先创建一个线程池，然后向线程池中提交了一个任务， submit提交任务后会被立即返回，而不会等到任务实际处理完成才会返回， 而任务提交后返回值便是 Future
， 通过 future我们可以调用 get() 方法阻塞式的获取返回结果。 也可以使用 isDone 获取任务是否完成


生产者线程在提交完任务后，此时它有两个选择，关注或者不关注处理结果。处理结果包括任务的返回值，也包含任务是否正确完成，中途 是否抛出异常等等。 future 模式提供一种机制，在消费者异步处理生产者提交的任务的情况下，生产者线程也可以拿到消费者线程的处理结果，
同时 通过 future 也可以取消掉处理中的任务。在实际的开发中，我们经常会遇到这种类似需求。 任务需要异步处理，同时又关心任务的处理结果。此时使用 future 是再合适不过了。

#### 1.2 future 如何被构建的 
future 是如何被创建的呢? 生产者线程提交给消费者线程池 任务时，线程池会构造一个实现了Future接口的对象FutureTask 。该对象相当于是消费者和生产者的桥梁，消费者通过FutureTask 存储任务的处理结果，更新任务的状态，未开始，正在处理，已完成等。而生产者拿到的 FutureTask 被转型为 Future
 接口，可以阻塞式获取任务的处理结果，非阻塞式获取任务处理状态。更细节的实现机制，读者可以参考 Jdk 中的 FutureTask 类。
 
#### 1.3 java之外的一些思考
  我一直将Future视为消费者线程和生产者线程的关于该任务的一个通道， java 中通过共享对象来进行跨线程通信，并且提供了各种工具来保证共享对象的线程安全性，future 是一个典型通过共享内存来通信的例子，而熟悉 go 语言的读者会想到，协程间通信的方式是通过 channel。就像go 语言信仰的那句话:不要通过共享内存来通信，而应该通过通信来共享内存
  go 所作的就是通过 channel，通过通信共享了内存，共享了数据。
  
 通过对 future 的示例，我们了解了 future 在任务生产者和消费者之间的起到的桥梁作用。但是我们解决的问题是。文中开头提到的任务处理三大阶段中的最后一个阶段
 任务完成的后置处理。而本文介绍的重点CompletableFuture 提供的编程模型，可以让我们随心所欲地优雅地处理后置结果。
 
### 2.任务结果的花式处理
  有两种可能生产者不需要关注的任务的处理结果。第一种可能:处理结果并不影响后续的业务逻辑。另一种，被提交的任务在结束前，会将自身的处理结果上报到其他结构中，例如 mq，db，redis 等等， 这些任务的处理结果会被其他的
  协调者或者调度者跟踪和监控。不再需要生产者关心。这样生产者只负责 生产并且提交任务，而完全不用关心任务的处理，和任务结果的处理。在这种编程模型中，实现了充分的解耦。但是也增加了系统的复杂度， 任务状态和结果需要额外的监控及管控， 这种处理方式场景复杂，吞吐量大的分布式系统中有着广泛的应用。
  
  但另外一种更简单的系统设计 要求生产者需要关心处理结果。 根据处理结果执行后续的任务处理。 CompletableFuture 正是为此而生。
  
  
#### 2.1 Future 的改造
   在第一节中我们简单介绍了 Future， 但是我们给的例子获取结果都是使用 get 阻塞式的获取，实际开发中，我们并不希望 生产者线程会被阻塞住， 但是又希望，当我们提交完任务后
   可以通过 Future处理结果?如何实现呢?
   在1.2中我们讨论 Future 是如何被构造的时候，曾说过 消费者线程在执行 Task后，会将处理结果 set  到 Future 中，那么我们为什么不利用 set 方法，为我们提供一种后置处理的机制呢?思路是在调用
   set 方法后执行一系列后置处理，这些后置处理是生产者在提交 Task 时指定的。这样虽然执行后置处理的线程并不是生产者线程，但实际上处理逻辑是有生产者指定的。
    CompletableFuture 基于这种机制为我们提供了很多后置处理的执行方式，同时又提供了很多整合多个 Future 的方法。我们可以使用 CompletableFuture 灵活的处理多个 Task协同处理的问题
  
#### 2.2 复杂任务的示例说明
  在某些业务场景中，任务处理并不是简单地执行一条 sql， 某些长任务需要被拆解为很多小任务，而这些小任务有些可以并行处理，有些是有依赖顺序的。假设有如下一个长任务
      
      Task A如下子任务
      1.  可并行处理的 Task1.1 Task1.2 Task1.3
      2.  依据第一步 Task1.1， 1.2.1.3  三个任务的结果，执行 Task2 
      3.  根据 Task2的结果.异步的执行Task 3.1
  
  TaskA 是一个比较复杂的任务，需要拆分多个子任务，其中子任务中也会涉及到子任务.如何保证这些任务的依赖关系，同时保证任务可以得到异步处理呢?
  
      例2.2      
              future1.thenCombine(future2， (args1， args2) -> {      ### Task 1
                  println(args1);
                  println(args2);
                  return "3";
              }).thenApply((res) -> {                               ### Task 2
                  println(res);
                  return "4";
              }).thenApplyAsync((res) -> {                          ### Task 3
                  println(res);
                  return "5";
              });
    
   
   在例2.2中 future1.future2  都完成时，执行了 Combine动作，combine 会生成新的 Future。新的 future 完成后将执行 thenApply， 对合并产生的结果再次处理，最后再次对结果处理，而此次处理则是异步执行，即后置处理的线程和任务的消费者线程不是同一个线程。
 
   例2.2 只是一个使用 CompletableFuture 的简单使用， CompletableFuture 为我们提供了非常多的方法， 笔者将其所有方法按照功能分类如下:
      
      1. 对一个或多个 Future 合并操作，生成一个新的 Future， 参考allOf，anyOf，runAsync， supplyAsync
      2. 为 Future 添加后置处理动作， thenAccept， thenApply， thenRun
      3. 两个人 Future 任一或全部完成时，执行后置动作 applyToEither， acceptEither， thenAcceptBothAsync， runAfterBoth，runAfterEither等
      4. 当 Future 完成条件满足时，异步或同步执行  后置处理动作。 thenApplyAsync， thenRunAsync。所有异步后置处理都会添加 Async 后缀
      5. 定义 Future 的处理顺序 thenCompose 协同存在依赖关系的 Future。，thenCombine。合并多个 Future的处理结果返回新的处理结果
      6. 异常处理 exceptionally ，如果任务处理过程中抛出了异常.
   
   我们需要明白 CompletableFuture 提供了一些方法组合新的 Future，组合条件依赖顺序执行，或并行执行。 提供另一些方法指定 Future 的完成条件，及要执行的后置处理，后置处理包括 apply， accept， run
   apply类型的后置处理带返回值，也就是要生成新的处理结果。 accept 代表对处理结果进行消费，但是并不产生新的处理结果，而 run 更加简单。既没有上一次处理结果的输入，也没有返回处理结果。
   通过三种类型的后置处理，可以组合一个链式处理的后置处理。 后置处理可以不由消费者线程执行，可在线程池中单独执行。这样从生产者，消费者，后置处理三个阶段都可以异步执行。
   
   CompletableFuture实现了 Future， 及 ComplatableStage 接口， 实现 Future 接口代表其本身可以作为生产者和消费者的"桥梁"， 而 ComplatableStage 接口定义了
   以上所有的组合条件，完成条件，后置处理的多种类型，等众多的 API， 可以说 Future 接口只是描述了单个任务处理的方式， 而 CompletableStage 接口更进一步的
   从实际的编程需求出发，满足了多个任务协同处理的场景需求，包括多个任务任一完成时， 全部完成时。 任务串行顺序执行， 并行执行。并且创造性的提出了 apply， accept， run  三种后置
   处理器的类型，本质上后置处理还是链式顺序执行的。这样在众多子任务的场景需求中， CompletableFuture可以很好的胜任
   
   由于 CompletableFuture的 API 众多，笔者只是按照自己的理解按照功能不同做了分类。读者如果更深入的理解还是需要实际动手，文末提供了非常不错的相关 API 使用教程
   
   
   具体 API 的使用还需要读者慢慢的摸索 http://www.importnew.com/28319.html