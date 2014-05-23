#!/usr/bin/env ruby

require 'json'
require 'ostruct'
require 'mail'


STATUS_FILE = 'job.lock'

def sys_busy?
  begin
    cpu_usage = `ps fuxw | awk '{ if ($3 ~ /^[0-9]/) {SUM +=$3}} END  {print SUM"%"}'`.to_f
    #cpu_usage = 0    
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

def clean_status(dir)
  File.delete(File.join(dir, STATUS_FILE))
end

def write_status(dir, status)
  File.open(File.join(dir, STATUS_FILE), 'w') do |f|
    f.write(status)
  end
end

def already_running?(dir)
  File.exists?(File.join(dir, STATUS_FILE))
end

if $0 == __FILE__
  usage = "Usage: #{$0} batch_job_dir"
  if ARGV.size != 1
    $stderr.puts usage
    exit
  else
    session_dir = File.realpath(ARGV[0])
    unless File.directory?(session_dir)
      $stderr.puts usage
      exit
    end
  end

  Dir.chdir(session_dir)

  exit if sys_busy?
  exit if already_running?(session_dir)

  Dir.foreach('./').sort_by { |x| File.stat(x).mtime }.reverse.each do |job|
    exit if sys_busy?
    exit if already_running?(session_dir)

    next unless job.start_with?('MFEprimer-2.0')

    write_status(session_dir, File.read(job))
    opts = OpenStruct.new
    File.read(job).each_line do |line|
      opt, value = line.strip.split(': ')
      opts[opt] = value
    end

    opts.out = File.join(__dir__, 'session', job)
    begin
      mfeprimer = File.join(__dir__, 'mfeprimer/MFEprimer.py')
      cmd = "#{mfeprimer} -i #{File.join(__dir__, opts.infile)} -o #{opts.out} -d #{File.join(__dir__, opts.database)} -k #{opts.k_value} --mono_conc=#{opts.mono_conc} --diva_conc=#{opts.diva_conc} --oligo_conc=#{opts.oligo_conc} --dntp_conc=#{opts.dntp_conc} --ppc=#{opts.ppc} --size_start=#{opts.size_start} --size_stop=#{opts.size_stop} --tm_start=#{opts.tm_start} --tm_stop=#{opts.tm_stop} --dg_start=#{opts.dg_start} --dg_stop=#{opts.dg_stop}"
      p cmd
      `#{cmd}`
      `zip #{opts.out}.zip #{opts.out}`
      File.delete(job)
    rescue
      clean_status(session_dir)
    end
 end
end
