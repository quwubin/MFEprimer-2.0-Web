#!/usr/bin/env ruby

require 'json'
require 'ostruct'
require 'mail'

TEMPLATE = 'template.fa'
TEMPLATE_CONFIG = 'template.fa.csv'
GLOBAL_SETTINGS = 'global_settings.json'
MPRIMER_OUT = 'mprimer_out.tsv'
MPRIMER_OUT_JSON = 'mprimer_out.json'
MPRIMER_OUT_YAML = 'mprimer_out.yaml'

STATUS_FILE = 'job.status'
SYS_STATUS_FILE = 'sys.status'
SYS_BUSY = 'Busy'
SYS_IDLE = 'Idle'

# Status flag
IN_QUEUE = 'In queue'
RUNNING = 'Running'
DONE = 'Done'
ERROR = 'Input error'

def input_ok?
  return false unless File.exists?(TEMPLATE)
  return false unless File.exists?(TEMPLATE_CONFIG)
  return false unless File.exists?(GLOBAL_SETTINGS)
  write_status(IN_QUEUE) unless File.exists?(STATUS_FILE)
  return true
end

def in_queue?
  return File.read(STATUS_FILE).chomp == IN_QUEUE
end

def sys_busy?
  begin
    # cpu_usage = `ps fuxw | awk '{ if ($3 ~ /^[0-9]/) {SUM +=$3}} END  {print SUM"%"}'`.to_f
    cpu_usage = 0    
  rescue Exception => e
    cpu_usage = 0    
  end

  if cpu_usage > 500
    return true
  else
    return false
  end
  #return File.read(SYS_STATUS_FILE).chomp == SYS_BUSY
end

def write_status(status, file=STATUS_FILE)
  File.open(file, 'w') do |f|
    f.write(status)
  end
end

def is_done?
  return File.read(STATUS_FILE).chomp == DONE
end

def is_error?
  return File.read(STATUS_FILE).chomp == ERROR
end

def run_mprimer(dir)
  write_status(RUNNING)
  global_para = JSON.parse(File.read(GLOBAL_SETTINGS))
  opts = Qu::Mprimer::default_options
  global_para.each_pair do |key, value|
    if opts.respond_to?(key)
      opts[key] = value
    end
  end

  opts.in = TEMPLATE
  opts.out = File.open(MPRIMER_OUT, 'w')
  $stderr = File.open(opts.out.path + '.log', 'w')

  begin
    #Qu::Mprimer::Runner.new(opts).run
    start = Time.now
    pool, failed, template_count = Qu::Mprimer::Design.new(opts).pick_primers
    pool = [] if pool[0].empty?
    tubes = []
    pool.each do |group|
      tm_list = []
      gc_list = []
      size_list = []
      group.each do |p|
        tm_list << p.fp.tm
        tm_list << p.rp.tm
        gc_list << p.fp.gc
        gc_list << p.rp.gc
        size_list << p.product.size
      end

      tube_status = {
        tm_mean: tm_list.mean.round(2),
        tm_stdev: tm_list.standard_deviation.round(2),
        gc_mean: gc_list.mean.round(2),
        gc_stdev: gc_list.standard_deviation.round(2),
        size_min: size_list.min,
        size_mean: size_list.mean.round(0),
        size_max: size_list.max,
        size: group.size,
      }

      primer_list = []

      group.each do |primer|
        fp = {
          seq: primer.fp.seq,
          tm: primer.fp.tm.round(2),
          gc: primer.fp.gc.round(2),
          pos: primer.fp.pos,
          penalty: primer.fp.penalty
        }
        rp = {
          seq: primer.rp.seq,
          tm: primer.rp.tm.round(2),
          gc: primer.rp.gc.round(2),
          pos: primer.rp.pos,
          penalty: primer.fp.penalty
        }
        product = {
          id: primer.product.id,
          seq: primer.product.seq,
          size: primer.product.seq.size
        }
        primer_list << {
          fp: fp, 
          rp: rp, 
          product: product
        }
      end
      tubes << {
        tube_status: tube_status,
        primer_list: primer_list,
      }
    end

    elapsed_time = Time.now - start

    results = {
      tubes: tubes,
      failed: failed,
      template_count: template_count,
      opts: opts.marshal_dump,
      elapsed_time: elapsed_time,
    }

    File.open(MPRIMER_OUT_JSON, 'w') do |fh|
      fh.write(JSON.dump(results))
    end

    Qu::Mprimer::Runner.new(opts).output(pool, failed, elapsed_time, template_count)
    #`tar cjf mprimer_out.tar.bz2 mprimer_out.tsv`
    write_status(DONE)

  # rescue
  #   write_status(ERROR)
  end
  opts.out.close

  `tar cjf #{MPRIMER_OUT}.tar.bz2 #{MPRIMER_OUT} #{MPRIMER_OUT}.log #{TEMPLATE_CONFIG}`
  if global_para.has_key?('email') 
    address = global_para['email']

    send_mail(address, dir) unless address.empty?
  end
end

def send_mail(address, dir)
  options = { :address    => "smtp.163.com",
    :user_name            => 'mprimer',
    :password             => 'wangting',
  }

  Mail.defaults do
    delivery_method :smtp, options
  end

  Mail.deliver do
    to address
    from 'mprimer@163.com'
    subject "Your job is done: #{dir}"
    body "http://biocompute.bmi.ac.cn/CZlab/mprimer/check?job_id=#{dir}"
  end
end

if $0 == __FILE__
  usage = "Usage: #{$0} batch_job_dir"
  if ARGV.size != 1
    $stderr.puts usage
    exit
  else
    session_dir = ARGV[0]
    unless File.directory?(session_dir)
      $stderr.puts usage
      exit
    end
  end

  Dir.chdir(session_dir)
  unless File.exists?(SYS_STATUS_FILE)
    write_status(SYS_IDLE, file = SYS_STATUS_FILE)
  end

  exit if sys_busy?

  Dir.foreach('./').sort_by { |x| File.stat(x).mtime }.reverse.each do |dir|
    exit if sys_busy?

    if dir == '.' or dir == '..'
      next
    end
    next if File.directory?(dir)
    Dir.chdir(dir)
    if input_ok? and in_queue?
      write_status(SYS_BUSY, file = "../#{SYS_STATUS_FILE}")
      begin
       run_mprimer(dir)
     rescue
       write_status(ERROR)
     end
   end
   Dir.chdir('../')
   write_status(SYS_IDLE, file = SYS_STATUS_FILE)
 end
end
